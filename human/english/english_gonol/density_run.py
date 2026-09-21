# === MODULE_BUILD ===
# id: english_gonol_corpus_native_density
#   module_name: density_run
#   module_kind: measurement
#   summary: exact per-scalar occurrence counts through every constructed occurrence relation of the verified v2 construct, recorded as semantic-valuation inputs at every scale
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, DensityError, DensityResult, build_density, run, iter_word_to_words_in_definitions, iter_characters_in_word_to_characters_in_definitions, relational_receipt
#   internal_surface: read-only construct inspection, exact Fraction arithmetic, canonical receipt serialization
#   auth_boundary: measures the already-constructed English Gonol v2 database; does not retokenize, normalize, or re-admit corpus text; supplies no geometry
#   storage_boundary: one caller-selected out directory with density.json and density.md
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_density_run
#   rollout: stack-local research measurement outside the construct; no canon or semantic measurement promotion
#   rollback: delete this module and its generated output directory
#   requires: english_gonol_full_construct
#   since: 2026-09-15
#   unresolved: what measured density does geometrically remains unresolved
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: density_counts_constructed_occurrence_relations
#   given: a verified English Gonol v2 construct.db
#   then: every letter count is taken from the constructed occurrence relations joined to shared character identities, never by retokenizing or normalizing source text
#   class: correctness
#   since: 2026-09-15
#
# id: density_is_determinable_at_every_scale
#   given: the v2 construct materializes character, word, definition, and semantic scales
#   then: the same per-scalar count is measured at every one of those scales through its own constructed occurrence relation
#   class: correctness
#   since: 2026-09-15
#
# id: density_fractions_are_exact
#   given: exact integer per-letter counts and an exact per-scale total
#   then: every frequency is recorded as an exact reduced Fraction of that scale's total
#   class: correctness
#   since: 2026-09-15
#
# id: density_ratios_are_reduced
#   given: any pair of letters with exact integer counts at one scale
#   then: the ratio between their counts is recorded reduced to lowest terms
#   class: correctness
#   since: 2026-09-15
#
# id: density_records_provenance_and_receipt
#   given: a construct manifest and measured database hash
#   then: corpus and builder hashes, the construct receipt, and a canonical density receipt are all recorded
#   class: correctness
#   since: 2026-09-15
#
# id: density_counts_are_semantic_valuation_inputs
#   given: a density result
#   then: the per-scale counts are recorded as exact semantic-valuation inputs without inventing a valuation weight, direction, or geometry
#   class: doctrine
#   since: 2026-09-15
#
# id: density_relational_scales_are_determinable_not_stored
#   given: word-to-words-in-definitions and characters-in-word-to-characters-in-definitions scales
#   then: each is streamed on demand from the construct and recorded as determinable with stored=false, never materialized into the density table
#   class: correctness
#   since: 2026-09-15
#
# id: density_relational_receipt_is_compact
#   given: one relational scale
#   then: streaming its rows yields a compact row count and sha256 digest without storing the rows
#   class: correctness
#   since: 2026-09-15
#
# id: density_stays_outside_the_construct
#   given: a density result
#   then: it is a separate measurement table that modifies no construct table and invents no geometry
#   class: doctrine
#   since: 2026-09-15
#
# id: density_fails_closed_on_wrong_construct_schema
#   given: a construct manifest whose schema is not english-gonol.full-construct
#   then: build_density raises DensityError
#   class: safety
#   since: 2026-09-15
# === END CONTRACTS ===

"""Corpus-native per-scale letter density from the constructed relations.

The English Gonol v2 construct materializes one shared identity per exact
character scalar and a constructed occurrence relation at every scale::

    character scale   -> characters identity (each admitted scalar exists once)
    word scale        -> word_characters ordered character references
    definition scale  -> definition_components word references plus whitespace
                         character references
    semantic scale    -> semantic_evidence target word references expanded
                         through their word_characters

This measurement reads only those constructed relations. Each admitted
character scalar gets an exact integer occurrence count at every scale, an
exact frequency fraction of that scale's total, and exact reduced pairwise
ratios between scalars at that scale. The per-scale counts are semantic
valuation inputs: they are determinable at any and every scale, with no
invented weight, direction, or geometry.

Nothing is retokenized, case-folded, normalized, or re-admitted; the generic
density table stays outside the construct.

hmmm: frequency becomes measured; what density does geometrically remains
unresolved.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator

SCHEMA = "english-gonol.corpus-native-density"
VERSION = "2.1.0"
CONSTRUCT_SCHEMA = "english-gonol.full-construct"

_HMMM = (
    "frequency becomes measured; "
    "what density does geometrically remains unresolved"
)

_SCALES = ("character", "word", "definition", "semantic")

_RELATIONAL_SCALES: dict[str, str] = {
    "word_to_words_in_definitions": (
        "for each origin word, exact counts of word identities appearing in "
        "its definitions through definition_components word references"
    ),
    "characters_in_word_to_characters_in_definitions": (
        "for each origin word, exact counts of character identities appearing "
        "in its definitions through definition_components (word references "
        "expanded through word_characters plus whitespace character references)"
    ),
}


class DensityError(ValueError):
    """Raised when the density measurement fails closed."""


@dataclass(frozen=True)
class DensityResult:
    schema: str
    version: str
    corpus: dict[str, Any]
    builder: dict[str, Any]
    semantic_valuation: dict[str, Any]
    scales: dict[str, dict[str, Any]]
    relational_scales: dict[str, dict[str, Any]]
    hmmm: str
    receipt_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "corpus": self.corpus,
            "builder": self.builder,
            "semantic_valuation": self.semantic_valuation,
            "scales": self.scales,
            "relational_scales": self.relational_scales,
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
        raise DensityError(f"construct manifest is not readable JSON: {path}") from exc
    if manifest.get("schema") != CONSTRUCT_SCHEMA:
        raise DensityError(f"construct manifest schema must be {CONSTRUCT_SCHEMA}")
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


def _reduced_ratio_text(a_count: int, b_count: int) -> str:
    if b_count == 0:
        return f"{a_count}/0"
    if a_count == 0:
        return f"0/{b_count}"
    ratio = Fraction(a_count, b_count)
    return f"{ratio.numerator}/{ratio.denominator}"


def _letters_from_counts(
    connection: sqlite3.Connection,
    counts_sql: str,
) -> tuple[list[tuple[str, int | None, int, str]], int]:
    """Run a per-character count query and return letter rows plus total.

    ``counts_sql`` must select ``c.scalar, c.public_position, COALESCE(x.cnt, 0)``
    ordered by ``c.id``.
    """

    rows = connection.execute(counts_sql).fetchall()
    if not rows:
        raise DensityError("constructed occurrence relations are empty")
    total = sum(count for _, _, count in rows)
    if total <= 0:
        raise DensityError("scale total must be positive")
    letters = [
        (
            scalar,
            public_position,
            count,
            f"{Fraction(count, total).numerator}/{Fraction(count, total).denominator}",
        )
        for scalar, public_position, count in rows
    ]
    return letters, total


def _ratios_for(
    letters: list[tuple[str, int | None, int, str]],
) -> list[tuple[str, str, str]]:
    ratios: list[tuple[str, str, str]] = []
    for left in range(len(letters)):
        for right in range(left + 1, len(letters)):
            ratios.append(
                (
                    letters[left][0],
                    letters[right][0],
                    _reduced_ratio_text(letters[left][2], letters[right][2]),
                )
            )
    return ratios


def _scale_record(
    relation: str,
    letters: list[tuple[str, int | None, int, str]],
    total: int,
) -> dict[str, Any]:
    return {
        "relation": relation,
        "total": total,
        "letters": [
            {
                "scalar": scalar,
                "public_position": public_position,
                "count": count,
                "frequency_fraction": fraction,
            }
            for scalar, public_position, count, fraction in letters
        ],
        "ratios": [
            {"a": a, "b": b, "reduced_ratio": ratio}
            for a, b, ratio in _ratios_for(letters)
        ],
    }


_CHARACTER_SCALE_SQL = """
SELECT c.scalar, c.public_position, 1 AS cnt
FROM characters AS c
ORDER BY c.id
"""

_WORD_SCALE_SQL = """
SELECT c.scalar, c.public_position, COALESCE(x.cnt, 0)
FROM characters AS c
LEFT JOIN (
    SELECT wc.character_id AS cid, COUNT(*) AS cnt
    FROM word_characters AS wc
    GROUP BY wc.character_id
) AS x ON x.cid = c.id
ORDER BY c.id
"""

_DEFINITION_SCALE_SQL = """
SELECT c.scalar, c.public_position, COALESCE(x.cnt, 0)
FROM characters AS c
LEFT JOIN (
    SELECT cid, SUM(cnt) AS cnt
    FROM (
        SELECT dc.character_id AS cid, COUNT(*) AS cnt
        FROM definition_components AS dc
        WHERE dc.character_id IS NOT NULL
        GROUP BY dc.character_id
        UNION ALL
        SELECT wc.character_id AS cid, COUNT(*) AS cnt
        FROM definition_components AS dc
        JOIN word_characters AS wc ON wc.word_id = dc.word_id
        WHERE dc.word_id IS NOT NULL
        GROUP BY wc.character_id
    )
    GROUP BY cid
) AS x ON x.cid = c.id
ORDER BY c.id
"""

_SEMANTIC_SCALE_SQL = """
SELECT c.scalar, c.public_position, COALESCE(x.cnt, 0)
FROM characters AS c
LEFT JOIN (
    SELECT wc.character_id AS cid, COUNT(*) AS cnt
    FROM semantic_evidence AS se
    JOIN word_characters AS wc ON wc.word_id = se.target_word_id
    GROUP BY wc.character_id
) AS x ON x.cid = c.id
ORDER BY c.id
"""


def _open_construct(construct_db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{construct_db}?mode=ro", uri=True)


def iter_word_to_words_in_definitions(
    construct_db: Path,
) -> Iterator[dict[str, Any]]:
    """Stream exact word-to-word definition counts on demand.

    One row per ``(origin word, target word)`` pair: the exact count of
    target word identities inside the origin word's definitions, taken only
    from ``definitions`` + ``definition_components`` word references.
    """

    connection = _open_construct(construct_db)
    try:
        cursor = connection.execute(
            """
            SELECT w.id AS word_id, w.surface AS surface,
                   dc.word_id AS target_word_id, COUNT(*) AS count
            FROM words AS w
            JOIN definitions AS d ON d.origin_word_id = w.id
            JOIN definition_components AS dc
              ON dc.definition_id = d.id AND dc.word_id IS NOT NULL
            GROUP BY w.id, dc.word_id
            ORDER BY w.id, dc.word_id
            """
        )
        for word_id, surface, target_word_id, count in cursor:
            yield {
                "word_id": word_id,
                "surface": surface,
                "target_word_id": target_word_id,
                "count": count,
            }
    finally:
        connection.close()


def iter_characters_in_word_to_characters_in_definitions(
    construct_db: Path,
) -> Iterator[dict[str, Any]]:
    """Stream exact character-to-character definition counts on demand.

    One row per ``(origin word, character scalar)`` pair: the exact count of
    character identities inside the origin word's definitions, taken only
    from ``definition_components`` — word references expanded through
    ``word_characters`` and whitespace character references taken directly.
    """

    connection = _open_construct(construct_db)
    try:
        cursor = connection.execute(
            """
            SELECT x.wid AS word_id, c.scalar AS scalar, SUM(x.cnt) AS count
            FROM (
                SELECT w.id AS wid, wc.character_id AS cid, COUNT(*) AS cnt
                FROM words AS w
                JOIN definitions AS d ON d.origin_word_id = w.id
                JOIN definition_components AS dc ON dc.definition_id = d.id
                JOIN word_characters AS wc ON wc.word_id = dc.word_id
                WHERE dc.word_id IS NOT NULL
                GROUP BY w.id, wc.character_id
                UNION ALL
                SELECT w.id AS wid, dc.character_id AS cid, COUNT(*) AS cnt
                FROM words AS w
                JOIN definitions AS d ON d.origin_word_id = w.id
                JOIN definition_components AS dc ON dc.definition_id = d.id
                WHERE dc.character_id IS NOT NULL
                GROUP BY w.id, dc.character_id
            ) AS x
            JOIN characters AS c ON c.id = x.cid
            GROUP BY x.wid, c.scalar
            ORDER BY x.wid, c.id
            """
        )
        for word_id, scalar, count in cursor:
            yield {"word_id": word_id, "scalar": scalar, "count": count}
    finally:
        connection.close()


def relational_receipt(construct_db: Path, scale: str) -> dict[str, Any]:
    """Stream one relational scale and return a compact digest, without storing it."""

    if scale not in _RELATIONAL_SCALES:
        raise DensityError(f"unknown relational scale: {scale}")
    if scale == "word_to_words_in_definitions":
        iterator = iter_word_to_words_in_definitions(construct_db)
    else:
        iterator = iter_characters_in_word_to_characters_in_definitions(construct_db)

    digest = sha256()
    rows = 0
    for row in iterator:
        digest.update(
            json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
        rows += 1
    return {
        "scale": scale,
        "description": _RELATIONAL_SCALES[scale],
        "stored": False,
        "rows": rows,
        "sha256": digest.hexdigest(),
    }


def build_density(construct_db: Path, construct_manifest: Path) -> DensityResult:
    """Measure per-scale letter density through the constructed relations only."""

    manifest = _load_manifest(construct_manifest)
    if not construct_db.is_file():
        raise DensityError(f"construct database does not exist: {construct_db}")

    construct_db_sha256 = _hash_file(construct_db)
    connection = sqlite3.connect(f"file:{construct_db}?mode=ro", uri=True)
    try:
        character_letters, character_total = _letters_from_counts(
            connection, _CHARACTER_SCALE_SQL
        )
        word_letters, word_total = _letters_from_counts(connection, _WORD_SCALE_SQL)
        definition_letters, definition_total = _letters_from_counts(
            connection, _DEFINITION_SCALE_SQL
        )
        semantic_letters, semantic_total = _letters_from_counts(
            connection, _SEMANTIC_SCALE_SQL
        )
    except sqlite3.Error as exc:
        raise DensityError(f"construct database is not readable: {exc}") from exc
    finally:
        connection.close()

    scales = {
        "character": _scale_record(
            "characters identity: each admitted scalar exists once",
            character_letters,
            character_total,
        ),
        "word": _scale_record(
            "word_characters: ordered character references inside word surfaces",
            word_letters,
            word_total,
        ),
        "definition": _scale_record(
            "definition_components: word references expanded through word_characters plus whitespace character references",
            definition_letters,
            definition_total,
        ),
        "semantic": _scale_record(
            "semantic_evidence: target word references expanded through word_characters",
            semantic_letters,
            semantic_total,
        ),
    }

    relational_scales = {
        name: {
            "description": description,
            "stored": False,
            "determinable": True,
            "iterator": (
                "iter_word_to_words_in_definitions"
                if name == "word_to_words_in_definitions"
                else "iter_characters_in_word_to_characters_in_definitions"
            ),
        }
        for name, description in _RELATIONAL_SCALES.items()
    }

    semantic_valuation = {
        "counts_are": (
            "exact per-scalar occurrence counts through the constructed "
            "occurrence relations at every scale"
        ),
        "determinable_at_scales": list(_SCALES) + list(_RELATIONAL_SCALES),
        "scale_totals": {
            "character": character_total,
            "word": word_total,
            "definition": definition_total,
            "semantic": semantic_total,
        },
        "valuation_weight": None,
        "hmmm": _HMMM,
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
        "semantic_valuation": semantic_valuation,
        "scales": scales,
        "relational_scales": relational_scales,
        "hmmm": _HMMM,
    }
    receipt = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return DensityResult(
        schema=SCHEMA,
        version=VERSION,
        corpus=manifest["corpus"],
        builder=payload["builder"],
        semantic_valuation=semantic_valuation,
        scales=scales,
        relational_scales=relational_scales,
        hmmm=_HMMM,
        receipt_sha256=receipt,
    )


def _render_markdown(result: DensityResult) -> str:
    lines = [
        "# English Gonol corpus-native per-scale letter density",
        "",
        "Generic measurement table outside the construct. Per-scalar counts are",
        "semantic-valuation inputs, determinable at any and every scale.",
        "",
        "## Provenance",
        "",
        f"- corpus: {result.corpus.get('repository')} @ {result.corpus.get('commit')}",
        f"- source tree sha256: {result.corpus.get('source_tree_sha256')}",
        f"- construct schema: {result.builder.get('construct_schema')}",
        f"- construct version: {result.builder.get('construct_version')}",
        f"- construct receipt: {result.builder.get('construct_receipt_sha256')}",
        f"- construct database sha256: {result.builder.get('construct_db_sha256')}",
        f"- density receipt: {result.receipt_sha256}",
        "",
        "## Semantic valuation",
        "",
        f"- counts: {result.semantic_valuation.get('counts_are')}",
        f"- determinable at scales: {', '.join(result.semantic_valuation.get('determinable_at_scales', []))}",
        f"- valuation weight: {result.semantic_valuation.get('valuation_weight')}",
        "",
        "## Scale totals",
        "",
        "| scale | total |",
        "|---|---:|",
    ]
    for scale in _SCALES:
        lines.append(f"| {scale} | {result.scales[scale]['total']} |")
    lines.extend(
        [
            "",
            "## Relational scales (determinable, not stored)",
            "",
        ]
    )
    for name, record in result.relational_scales.items():
        lines.extend(
            [
                f"- {name}: {record['description']}",
                f"  stored: {record['stored']}, determinable: {record['determinable']}",
            ]
        )
    for scale in _SCALES:
        record = result.scales[scale]
        lines.extend(
            [
                "",
                f"## {scale.capitalize()} scale counts",
                "",
                f"Relation: {record['relation']}",
                "",
                "| scalar | public_position | count | frequency_fraction |",
                "|---|---:|---:|---|",
            ]
        )
        for letter in record["letters"]:
            scalar, public_position, count, fraction = letter
            display = scalar if scalar != " " else "` `"
            lines.append(f"| {display} | {public_position} | {count} | {fraction} |")
        lines.extend(
            [
                "",
                f"Reduced pairwise ratios ({len(record['ratios'])} pairs) are in `density.json`.",
            ]
        )
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
) -> DensityResult:
    """Build the density measurement and write ``density.json`` and ``density.md``."""

    result = build_density(construct_db, construct_manifest)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "density.json"
    markdown_path = out_dir / "density.md"
    if not overwrite and (json_path.exists() or markdown_path.exists()):
        raise DensityError(f"output files already exist in {out_dir}; pass --overwrite")
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
    parser.add_argument("--out-dir", required=True, help="density output directory")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = run(
            Path(args.construct_db),
            Path(args.construct_manifest),
            Path(args.out_dir),
            overwrite=args.overwrite,
        )
    except DensityError as exc:
        raise SystemExit(f"density error: {exc}") from exc

    print(json.dumps(
        {
            "schema": result.schema,
            "version": result.version,
            "scale_totals": result.semantic_valuation["scale_totals"],
            "receipt_sha256": result.receipt_sha256,
            "hmmm": result.hmmm,
        },
        sort_keys=True,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
