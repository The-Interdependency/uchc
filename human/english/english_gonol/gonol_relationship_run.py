# === MODULE_BUILD ===
# id: english_gonol_gonol_relationships
#   module_name: gonol_relationship_run
#   module_kind: measurement
#   summary: exact census of every relationship kind between closed gonols in the verified v2 construct plus per-gonol scale participation, determinable at any scale and never stored as new tables
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, GonolRelationshipError, GonolRelationshipResult, build_relationship_census, iter_word_participation, iter_character_cooccurrence, run
#   internal_surface: read-only construct inspection, exact COUNT arithmetic, canonical receipt serialization
#   auth_boundary: measures the already-constructed English Gonol v2 database; does not retokenize, normalize, or re-admit corpus text; supplies no geometry
#   storage_boundary: one caller-selected out directory with gonol-relationships.json and gonol-relationships.md
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_gonol_relationship_run
#   rollout: stack-local research measurement outside the construct; no canon or semantic measurement promotion
#   rollback: delete this module and its generated output directory
#   requires: english_gonol_full_construct, english_gonol_corpus_native_density
#   since: 2026-09-15
#   unresolved: what the measured relationships do geometrically remains unresolved
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: relationships_census_covers_every_constructed_relation
#   given: the verified v2 construct tables
#   then: every relationship kind between closed gonols materialized in the construct is counted exactly from its own constructed relation
#   class: correctness
#   since: 2026-09-15
#
# id: relationships_are_determinable_not_stored
#   given: sizable relationship streams (word participation, character co-occurrence)
#   then: they are streamed on demand from the construct and recorded with stored=false
#   class: correctness
#   since: 2026-09-15
#
# id: relationships_record_scale_participation
#   given: the closed gonols of the construct
#   then: each character records exact participation across word, definition, and semantic scales
#   class: correctness
#   since: 2026-09-15
#
# id: relationships_record_provenance_and_receipt
#   given: a construct manifest and measured database hash
#   then: corpus and builder hashes and a canonical receipt are recorded
#   class: correctness
#   since: 2026-09-15
#
# id: relationships_stay_outside_the_construct
#   given: a relationship result
#   then: it modifies no construct table and invents no geometry
#   class: doctrine
#   since: 2026-09-15
# === END CONTRACTS ===

"""Exact relationship census between atomic-at-any-scale gonols.

Closed gonols participate at any admissible scale without reopening. The v2
construct materializes the relationships between those closed gonols in its
own tables. This measurement reads only those tables and records:

* a census of every relationship kind, each with an exact row count;
* per-character scale participation (word, definition, semantic);
* per-word scale participation as an on-demand stream (not stored);
* within-word character co-occurrence pairs as an on-demand stream (not stored).

Nothing is retokenized, normalized, or re-admitted; no new table is created.
The result stays outside the construct and supplies no geometry.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator

SCHEMA = "english-gonol.gonol-relationships"
VERSION = "1.0.0"
CONSTRUCT_SCHEMA = "english-gonol.full-construct"

_HMMM = (
    "relationships are measured; "
    "what those relationships do geometrically remains unresolved"
)


class GonolRelationshipError(ValueError):
    """Raised when the relationship census fails closed."""


@dataclass(frozen=True)
class GonolRelationshipResult:
    schema: str
    version: str
    corpus: dict[str, Any]
    builder: dict[str, Any]
    census: tuple[tuple[str, str, int], ...]
    character_participation: tuple[dict[str, Any], ...]
    determinable_not_stored: dict[str, Any]
    hmmm: str
    receipt_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "corpus": self.corpus,
            "builder": self.builder,
            "census": [
                {"kind": kind, "relation": relation, "rows": rows}
                for kind, relation, rows in self.census
            ],
            "character_participation": list(self.character_participation),
            "determinable_not_stored": self.determinable_not_stored,
            "hmmm": self.hmmm,
            "receipt_sha256": self.receipt_sha256,
        }

    def canonical_bytes(self) -> bytes:
        payload = self.as_dict()
        payload.pop("receipt_sha256", None)
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def receipt_bytes(self) -> bytes:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GonolRelationshipError(f"construct manifest is not readable JSON: {path}") from exc
    if manifest.get("schema") != CONSTRUCT_SCHEMA:
        raise GonolRelationshipError(f"construct manifest schema must be {CONSTRUCT_SCHEMA}")
    return manifest


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(8 * 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _open_construct(construct_db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{construct_db}?mode=ro", uri=True)


_CENSUS_QUERIES: tuple[tuple[str, str, str], ...] = (
    (
        "character_in_word",
        "word_characters: ordered character references inside word surfaces",
        "SELECT COUNT(*) FROM word_characters",
    ),
    (
        "word_origin_definition",
        "definitions.origin_word_id: each definition is word-anchored",
        "SELECT COUNT(*) FROM definitions",
    ),
    (
        "definition_to_word_component",
        "definition_components: word references inside definitions",
        "SELECT COUNT(*) FROM definition_components WHERE word_id IS NOT NULL",
    ),
    (
        "definition_to_character_component",
        "definition_components: whitespace character references inside definitions",
        "SELECT COUNT(*) FROM definition_components WHERE character_id IS NOT NULL",
    ),
    (
        "definition_chain_previous",
        "definitions.previous_definition_id: sequential word -> D1 -> D2 -> ... topology",
        "SELECT COUNT(*) FROM definitions WHERE previous_definition_id IS NOT NULL",
    ),
    (
        "semantic_evidence_target",
        "semantic_evidence.target_word_id: definition -> target word evidence",
        "SELECT COUNT(*) FROM semantic_evidence",
    ),
    (
        "word_to_words_in_definitions",
        "origin word -> target word identities in its definitions (streamed)",
        "SELECT COUNT(*) FROM ("
        "SELECT w.id, dc.word_id FROM words AS w "
        "JOIN definitions AS d ON d.origin_word_id = w.id "
        "JOIN definition_components AS dc ON dc.definition_id = d.id AND dc.word_id IS NOT NULL "
        "GROUP BY w.id, dc.word_id)",
    ),
    (
        "characters_in_word_to_characters_in_definitions",
        "origin word -> character identities in its definitions (streamed)",
        "SELECT COUNT(*) FROM ("
        "SELECT x.wid, c.scalar FROM ("
        "SELECT w.id AS wid, wc.character_id AS cid FROM words AS w "
        "JOIN definitions AS d ON d.origin_word_id = w.id "
        "JOIN definition_components AS dc ON dc.definition_id = d.id "
        "JOIN word_characters AS wc ON wc.word_id = dc.word_id WHERE dc.word_id IS NOT NULL "
        "UNION ALL "
        "SELECT w.id AS wid, dc.character_id AS cid FROM words AS w "
        "JOIN definitions AS d ON d.origin_word_id = w.id "
        "JOIN definition_components AS dc ON dc.definition_id = d.id "
        "WHERE dc.character_id IS NOT NULL) AS x "
        "JOIN characters AS c ON c.id = x.cid GROUP BY x.wid, c.scalar)",
    ),
    (
        "character_cooccurrence_within_word",
        "unordered character pairs sharing one word surface (streamed)",
        "SELECT SUM(length * (length - 1) / 2) FROM ("
        "SELECT COUNT(*) AS length FROM word_characters GROUP BY word_id)",
    ),
)


_CHARACTER_PARTICIPATION_SQL = """
SELECT c.id AS character_id, c.scalar AS scalar, c.public_position AS public_position,
       COALESCE(wc.word_count, 0) AS word_count,
       COALESCE(d1.cnt, 0) + COALESCE(d2.cnt, 0) AS definition_count,
       COALESCE(se.cnt, 0) AS semantic_count
FROM characters AS c
LEFT JOIN (
    SELECT character_id, COUNT(DISTINCT word_id) AS word_count
    FROM word_characters
    GROUP BY character_id
) AS wc ON wc.character_id = c.id
LEFT JOIN (
    SELECT dc.character_id AS cid, COUNT(DISTINCT dc.definition_id) AS cnt
    FROM definition_components AS dc
    WHERE dc.character_id IS NOT NULL
    GROUP BY dc.character_id
) AS d1 ON d1.cid = c.id
LEFT JOIN (
    SELECT wc.character_id AS cid, COUNT(DISTINCT dc.definition_id) AS cnt
    FROM definition_components AS dc
    JOIN word_characters AS wc ON wc.word_id = dc.word_id
    WHERE dc.word_id IS NOT NULL
    GROUP BY wc.character_id
) AS d2 ON d2.cid = c.id
LEFT JOIN (
    SELECT wc.character_id AS cid, COUNT(DISTINCT se.id) AS cnt
    FROM semantic_evidence AS se
    JOIN word_characters AS wc ON wc.word_id = se.target_word_id
    GROUP BY wc.character_id
) AS se ON se.cid = c.id
ORDER BY c.id
"""


def iter_word_participation(construct_db: Path) -> Iterator[dict[str, Any]]:
    """Stream per-word scale participation on demand (not stored)."""

    connection = _open_construct(construct_db)
    try:
        cursor = connection.execute(
            """
            SELECT w.id AS word_id, w.surface AS surface,
                   (SELECT COUNT(*) FROM word_characters AS wc
                    WHERE wc.word_id = w.id) AS character_count,
                   (SELECT COUNT(*) FROM definitions AS d
                    WHERE d.origin_word_id = w.id) AS definitions_originated,
                   (SELECT COUNT(*) FROM definition_components AS dc
                    WHERE dc.word_id = w.id) AS definitions_containing,
                   (SELECT COUNT(*) FROM semantic_evidence AS se
                    WHERE se.target_word_id = w.id) AS semantic_targets
            FROM words AS w
            ORDER BY w.id
            """
        )
        for word_id, surface, character_count, definitions_originated, definitions_containing, semantic_targets in cursor:
            yield {
                "word_id": word_id,
                "surface": surface,
                "character_count": character_count,
                "definitions_originated": definitions_originated,
                "definitions_containing": definitions_containing,
                "semantic_targets": semantic_targets,
            }
    finally:
        connection.close()


def iter_character_cooccurrence(construct_db: Path) -> Iterator[dict[str, Any]]:
    """Stream within-word unordered character pairs on demand (not stored)."""

    connection = _open_construct(construct_db)
    try:
        cursor = connection.execute(
            """
            SELECT wc1.character_id AS a_id, wc2.character_id AS b_id, COUNT(*) AS count
            FROM word_characters AS wc1
            JOIN word_characters AS wc2
              ON wc2.word_id = wc1.word_id AND wc2.ordinal > wc1.ordinal
            GROUP BY wc1.character_id, wc2.character_id
            ORDER BY wc1.character_id, wc2.character_id
            """
        )
        for a_id, b_id, count in cursor:
            yield {"a_character_id": a_id, "b_character_id": b_id, "count": count}
    finally:
        connection.close()


def build_relationship_census(
    construct_db: Path,
    construct_manifest: Path,
) -> GonolRelationshipResult:
    """Count every relationship kind and per-character scale participation."""

    manifest = _load_manifest(construct_manifest)
    if not construct_db.is_file():
        raise GonolRelationshipError(f"construct database does not exist: {construct_db}")

    construct_db_sha256 = _hash_file(construct_db)
    connection = _open_construct(construct_db)
    try:
        census_rows: list[tuple[str, str, int]] = []
        for kind, relation, sql in _CENSUS_QUERIES:
            count = connection.execute(sql).fetchone()[0]
            census_rows.append((kind, relation, int(count)))

        participation_rows = connection.execute(_CHARACTER_PARTICIPATION_SQL).fetchall()
    except sqlite3.Error as exc:
        raise GonolRelationshipError(f"construct database is not readable: {exc}") from exc
    finally:
        connection.close()

    character_participation = tuple(
        {
            "character_id": character_id,
            "scalar": scalar,
            "public_position": public_position,
            "words_containing": word_count,
            "definitions_containing": definition_count,
            "semantic_targets_containing": semantic_count,
        }
        for character_id, scalar, public_position, word_count, definition_count, semantic_count in participation_rows
    )

    determinable_not_stored = {
        "word_participation": {
            "description": "per-word character_count, definitions_originated, definitions_containing, semantic_targets",
            "stored": False,
            "iterator": "iter_word_participation",
        },
        "character_cooccurrence_within_word": {
            "description": "unordered character pairs sharing one word surface with exact pair counts",
            "stored": False,
            "iterator": "iter_character_cooccurrence",
        },
    }

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "version": VERSION,
        "corpus": manifest["corpus"],
        "builder": {
            "construct_schema": manifest["schema"],
            "construct_version": manifest["version"],
            "construct_receipt_sha256": manifest.get("receipt_sha256"),
            "construct_db_sha256": construct_db_sha256,
            "ucns_commit": manifest.get("ucns", {}).get("commit"),
            "public_gonol_sha256": manifest.get("ucns", {}).get("public_gonol_sha256"),
        },
        "census": [
            {"kind": kind, "relation": relation, "rows": rows}
            for kind, relation, rows in census_rows
        ],
        "character_participation": list(character_participation),
        "determinable_not_stored": determinable_not_stored,
        "hmmm": _HMMM,
    }
    receipt = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return GonolRelationshipResult(
        schema=SCHEMA,
        version=VERSION,
        corpus=manifest["corpus"],
        builder=payload["builder"],
        census=tuple(census_rows),
        character_participation=character_participation,
        determinable_not_stored=determinable_not_stored,
        hmmm=_HMMM,
        receipt_sha256=receipt,
    )


def _render_markdown(result: GonolRelationshipResult) -> str:
    lines = [
        "# English Gonol gonol relationship census",
        "",
        "Generic measurement table outside the construct.",
        "",
        "## Provenance",
        "",
        f"- corpus: {result.corpus.get('repository')} @ {result.corpus.get('commit')}",
        f"- construct receipt: {result.builder.get('construct_receipt_sha256')}",
        f"- construct database sha256: {result.builder.get('construct_db_sha256')}",
        f"- relationship receipt: {result.receipt_sha256}",
        "",
        "## Relationship census",
        "",
        "| kind | rows |",
        "|---|---:|",
    ]
    for kind, relation, rows in result.census:
        lines.append(f"| {kind} | {rows} |")
    lines.extend(
        [
            "",
            "## Character scale participation",
            "",
            "| scalar | public_position | words | definitions | semantic targets |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in result.character_participation:
        display = row["scalar"] if row["scalar"] != " " else "` `"
        lines.append(
            f"| {display} | {row['public_position']} | {row['words_containing']} | "
            f"{row['definitions_containing']} | {row['semantic_targets_containing']} |"
        )
    lines.extend(
        [
            "",
            "## Determinable, not stored",
            "",
        ]
    )
    for name, record in result.determinable_not_stored.items():
        lines.append(f"- {name}: {record['description']}")
        lines.append(f"  stored: {record['stored']}")
    lines.extend(
        [
            "",
            "## hmmm",
            "",
            result.hmmm,
            "",
        ]
    )
    return "\n".join(lines)


def run(
    construct_db: Path,
    construct_manifest: Path,
    out_dir: Path,
    *,
    overwrite: bool = False,
) -> GonolRelationshipResult:
    """Build the census and write ``gonol-relationships.json`` and ``gonol-relationships.md``."""

    result = build_relationship_census(construct_db, construct_manifest)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "gonol-relationships.json"
    markdown_path = out_dir / "gonol-relationships.md"
    if not overwrite and (json_path.exists() or markdown_path.exists()):
        raise GonolRelationshipError(f"output files already exist in {out_dir}; pass --overwrite")
    json_path.write_text(
        result.receipt_bytes().decode("utf-8") + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(result), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--construct-db", required=True, help="English Gonol v2 construct.db path")
    parser.add_argument("--construct-manifest", required=True, help="construct manifest.json path")
    parser.add_argument("--out-dir", required=True, help="relationship census output directory")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = run(
            Path(args.construct_db),
            Path(args.construct_manifest),
            Path(args.out_dir),
            overwrite=args.overwrite,
        )
    except GonolRelationshipError as exc:
        raise SystemExit(f"relationship error: {exc}") from exc

    print(json.dumps(
        {
            "schema": result.schema,
            "version": result.version,
            "census": {kind: rows for kind, _, rows in result.census},
            "characters": len(result.character_participation),
            "receipt_sha256": result.receipt_sha256,
            "hmmm": result.hmmm,
        },
        sort_keys=True,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
