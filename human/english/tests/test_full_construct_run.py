# === CHECKS ===
# id: check_full_construct_identity_reuse
#   proves: full_construct_has_one_character_identity, full_construct_has_one_word_identity
#   call: self::test_one_character_and_one_word_identity_are_reused
#   requires: python3
#   timeout: 30
#   mutates: filesystem
#   cleanup: tempdir_teardown
#
# id: check_full_construct_definition_topology
#   proves: full_construct_definitions_share_word_origin, full_construct_preserves_both_definition_topologies
#   call: self::test_definitions_share_origin_and_preserve_direct_and_chain_topology
#   requires: python3
#   timeout: 30
#   mutates: filesystem
#   cleanup: tempdir_teardown
#
# id: check_full_construct_exact_components
#   proves: full_construct_preserves_exact_definition_components, full_construct_keeps_probability_evidence_distinct
#   call: self::test_definition_components_reconstruct_exact_source_and_keep_evidence_distinct
#   requires: python3
#   timeout: 30
#   mutates: filesystem
#   cleanup: tempdir_teardown
#
# id: check_full_construct_no_evidence_promotion
#   proves: full_construct_does_not_promote_evidence_to_gonols, full_construct_never_invents_geometry
#   call: self::test_no_old_singleton_atlas_or_invented_geometry_exists
#   requires: python3
#   timeout: 30
#   mutates: filesystem
#   cleanup: tempdir_teardown
#
# id: check_full_construct_logical_replay
#   proves: full_construct_replays_logically
#   call: self::test_logical_receipt_is_deterministic_and_detects_tamper
#   requires: python3
#   timeout: 30
#   mutates: filesystem
#   cleanup: tempdir_teardown
# === END CHECKS ===

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from english_gonol.full_construct_run import (
    DEFINITION_COMPONENT_RULE,
    GEOMETRY_STATE,
    HMMM,
    RESOLUTION_RULE,
    SCHEMA,
    VERSION,
    FullConstructError,
    build_construct,
    verify_replay,
)
from english_gonol.language.source import (
    LexemeRecord,
    SenseRecord,
    SynsetRecord,
    WordnetSnapshot,
)


def _snapshot() -> WordnetSnapshot:
    # The intentionally non-lexicographic sense order is load-bearing evidence.
    return WordnetSnapshot(
        lexemes=(
            LexemeRecord(
                lemma="alpha",
                part_of_speech="n",
                forms=(),
                senses=(
                    SenseRecord(
                        sense_id="z-sense",
                        synset_id="s-z",
                        relations=(("also", ("other-sense",)),),
                    ),
                    SenseRecord(
                        sense_id="a-sense",
                        synset_id="s-a",
                        relations=(),
                    ),
                ),
            ),
            LexemeRecord(
                lemma="other",
                part_of_speech="n",
                forms=(),
                senses=(
                    SenseRecord(
                        sense_id="other-sense",
                        synset_id="s-other",
                        relations=(),
                    ),
                ),
            ),
        ),
        synsets=(
            SynsetRecord(
                synset_id="s-a",
                part_of_speech="n",
                members=("alpha",),
                definitions=("second\talpha",),
                relations=(),
            ),
            SynsetRecord(
                synset_id="s-other",
                part_of_speech="n",
                members=("other",),
                definitions=("another word",),
                relations=(),
            ),
            SynsetRecord(
                synset_id="s-z",
                part_of_speech="n",
                members=("alpha", "other"),
                definitions=("alpha letter alpha.",),
                relations=(("similar", ("s-other",)),),
            ),
        ),
        source_tree_sha256="0" * 64,
        source_file_count=3,
    )


def _public_position(scalar: str) -> int | None:
    # Fixture only; production run verifies exact UCNS carrier authority.
    return ord(scalar) % 157


def _build(path: Path) -> dict:
    return build_construct(
        _snapshot(),
        db_path=path,
        public_position=_public_position,
    )


def _table_names(db: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def _component_text(db: sqlite3.Connection, definition_id: int) -> str:
    parts: list[str] = []
    rows = db.execute(
        "SELECT dc.kind, dc.word_id, dc.character_id "
        "FROM definition_components dc WHERE dc.definition_id=? ORDER BY dc.ordinal",
        (definition_id,),
    )
    for kind, word_id, character_id in rows:
        if kind == "word":
            parts.append(
                db.execute("SELECT surface FROM words WHERE id=?", (word_id,)).fetchone()[0]
            )
        else:
            parts.append(
                db.execute("SELECT scalar FROM characters WHERE id=?", (character_id,)).fetchone()[0]
            )
    return "".join(parts)


def test_one_character_and_one_word_identity_are_reused(tmp_path: Path) -> None:
    db_path = tmp_path / "construct.db"
    _build(db_path)
    db = sqlite3.connect(db_path)
    try:
        alpha_id = db.execute("SELECT id FROM words WHERE surface='alpha'").fetchone()[0]
        assert db.execute("SELECT COUNT(*) FROM words WHERE surface='alpha'").fetchone()[0] == 1
        assert {
            row[0]
            for row in db.execute(
                "SELECT DISTINCT origin_word_id FROM definitions "
                "WHERE sense_id IN ('z-sense','a-sense')"
            )
        } == {alpha_id}
        assert db.execute(
            "SELECT COUNT(*) FROM definition_components "
            "WHERE kind='word' AND word_id=?",
            (alpha_id,),
        ).fetchone()[0] >= 2

        letter_id = db.execute("SELECT id FROM words WHERE surface='letter'").fetchone()[0]
        character_ids = [
            row[0]
            for row in db.execute(
                "SELECT character_id FROM word_characters WHERE word_id=? ORDER BY ordinal",
                (letter_id,),
            )
        ]
        assert character_ids[1] == character_ids[4]
        assert character_ids[2] == character_ids[3]
        assert db.execute("SELECT COUNT(*) FROM characters WHERE scalar='t'").fetchone()[0] == 1
    finally:
        db.close()


def test_definitions_share_origin_and_preserve_direct_and_chain_topology(tmp_path: Path) -> None:
    db_path = tmp_path / "construct.db"
    _build(db_path)
    db = sqlite3.connect(db_path)
    try:
        alpha_id = db.execute("SELECT id FROM words WHERE surface='alpha'").fetchone()[0]
        definitions = db.execute(
            "SELECT id, origin_word_id, ordinal, sense_id, previous_definition_id "
            "FROM definitions WHERE origin_word_id=? ORDER BY ordinal",
            (alpha_id,),
        ).fetchall()
        assert [(row[2], row[3]) for row in definitions] == [
            (1, "z-sense"),
            (2, "a-sense"),
        ]
        assert all(row[1] == alpha_id for row in definitions)
        assert definitions[0][4] is None
        assert definitions[1][4] == definitions[0][0]
    finally:
        db.close()


def test_definition_components_reconstruct_exact_source_and_keep_evidence_distinct(tmp_path: Path) -> None:
    db_path = tmp_path / "construct.db"
    _build(db_path)
    db = sqlite3.connect(db_path)
    try:
        first = db.execute(
            "SELECT id, text FROM definitions WHERE sense_id='z-sense'"
        ).fetchone()
        assert _component_text(db, first[0]) == first[1] == "alpha letter alpha."
        rows = db.execute(
            "SELECT dc.kind, w.surface, c.scalar, dc.start_offset, dc.end_offset "
            "FROM definition_components dc "
            "LEFT JOIN words w ON w.id=dc.word_id "
            "LEFT JOIN characters c ON c.id=dc.character_id "
            "WHERE dc.definition_id=? ORDER BY dc.ordinal",
            (first[0],),
        ).fetchall()
        assert rows == [
            ("word", "alpha", None, 0, 5),
            ("character", None, " ", 5, 6),
            ("word", "letter", None, 6, 12),
            ("character", None, " ", 12, 13),
            ("word", "alpha.", None, 13, 19),
        ]

        second = db.execute(
            "SELECT id, text FROM definitions WHERE sense_id='a-sense'"
        ).fetchone()
        assert _component_text(db, second[0]) == second[1] == "second\talpha"
        tab_id = db.execute("SELECT id FROM characters WHERE scalar=?", ("\t",)).fetchone()[0]
        assert db.execute(
            "SELECT COUNT(*) FROM definition_components "
            "WHERE definition_id=? AND kind='character' AND character_id=?",
            (second[0], tab_id),
        ).fetchone()[0] == 1

        other_id = db.execute("SELECT id FROM words WHERE surface='other'").fetchone()[0]
        evidence = db.execute(
            "SELECT channel, relation, target_word_id, target_ref "
            "FROM semantic_evidence WHERE definition_id=? ORDER BY id",
            (first[0],),
        ).fetchall()
        assert ("sense", "also", other_id, "other-sense") in evidence
        assert ("synset", "similar", other_id, "s-other") in evidence
        assert ("synset-membership", "co-member", other_id, "other") in evidence

        meta = dict(db.execute("SELECT key, value FROM meta"))
        assert meta["geometry_state"] == GEOMETRY_STATE
        assert meta["resolution_rule"] == RESOLUTION_RULE
        assert meta["definition_component_rule"] == DEFINITION_COMPONENT_RULE
        assert json.loads(meta["definition_topologies"]) == ["direct", "chain"]
        assert json.loads(meta["evidence_channels"]) == [
            "ordinal",
            "semantic",
            "sentence-context",
        ]
        assert HMMM in meta["hmmm"]
    finally:
        db.close()


def test_no_old_singleton_atlas_or_invented_geometry_exists(tmp_path: Path) -> None:
    db_path = tmp_path / "construct.db"
    _build(db_path)
    db = sqlite3.connect(db_path)
    try:
        assert _table_names(db) == {
            "meta",
            "characters",
            "words",
            "word_characters",
            "definitions",
            "definition_components",
            "semantic_evidence",
            "unresolved_semantic_evidence",
        }
        forbidden_fragments = {
            "weight",
            "vector",
            "coordinate",
            "center",
            "radius",
            "tangent",
            "motion",
        }
        for table in _table_names(db):
            columns = {
                row[1].lower()
                for row in db.execute(f"PRAGMA table_info({table})")
            }
            assert not any(
                fragment in column
                for column in columns
                for fragment in forbidden_fragments
            )
        for forbidden in (
            "senses",
            "synsets",
            "sentences",
            "occurrences",
            "relation_circles",
            "tangencies",
        ):
            assert forbidden not in _table_names(db)
    finally:
        db.close()


def test_logical_receipt_is_deterministic_and_detects_tamper(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()

    first = _build(first_dir / "construct.db")
    second = _build(second_dir / "construct.db")
    assert first["receipt_sha256"] == second["receipt_sha256"]

    manifest = {
        "schema": SCHEMA,
        "version": VERSION,
        "construct_file": "construct.db",
        "receipt_sha256": first["receipt_sha256"],
    }
    (first_dir / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    assert verify_replay(first_dir)["receipt_sha256"] == first["receipt_sha256"]

    db = sqlite3.connect(first_dir / "construct.db")
    try:
        db.execute("UPDATE words SET surface='tampered' WHERE surface='alpha'")
        db.commit()
    finally:
        db.close()

    with pytest.raises(FullConstructError, match="receipt mismatch"):
        verify_replay(first_dir)
