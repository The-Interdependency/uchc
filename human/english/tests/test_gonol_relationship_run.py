# === CHECKS ===
# id: check_relationships_census_covers_every_constructed_relation
#   proves: relationships_census_covers_every_constructed_relation
#   call: self::test_census_counts_every_constructed_relation
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_relationships_are_determinable_not_stored
#   proves: relationships_are_determinable_not_stored
#   call: self::test_sizable_streams_are_determinable_not_stored
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_relationships_record_scale_participation
#   proves: relationships_record_scale_participation
#   call: self::test_character_scale_participation_is_exact
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_relationships_record_provenance_and_receipt
#   proves: relationships_record_provenance_and_receipt
#   call: self::test_provenance_and_receipt_are_recorded
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_relationships_stay_outside_the_construct
#   proves: relationships_stay_outside_the_construct
#   call: self::test_stays_outside_the_construct
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

from hashlib import sha256
import json
import sqlite3
from pathlib import Path

import pytest

from english_gonol.gonol_relationship_run import (
    SCHEMA,
    VERSION,
    GonolRelationshipError,
    build_relationship_census,
    iter_character_cooccurrence,
    iter_word_participation,
    run,
)

CONSTRUCT_SCHEMA = "english-gonol.full-construct"


def _manifest() -> dict[str, object]:
    return {
        "schema": CONSTRUCT_SCHEMA,
        "version": "2.0.0",
        "receipt_sha256": "receipt-123",
        "corpus": {
            "repository": "globalwordnet/english-wordnet",
            "commit": "dc343f2683279ecbb13fab4e2fd778d7b162d287",
            "source_tree_sha256": "tree-123",
            "tag": "2025-edition",
        },
        "ucns": {
            "commit": "4f863ad37096b7baab8f62820ad5cb937b62a3a7",
            "public_gonol_sha256": "gonol-123",
        },
    }


def _make_construct(tmp_path: Path) -> tuple[Path, Path]:
    db_path = tmp_path / "construct.db"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest()), encoding="utf-8")

    connection = sqlite3.connect(db_path)
    connection.execute(
        "CREATE TABLE characters (id INTEGER PRIMARY KEY, scalar TEXT NOT NULL, public_position INTEGER)"
    )
    connection.execute(
        "CREATE TABLE words (id INTEGER PRIMARY KEY, surface TEXT NOT NULL)"
    )
    connection.execute(
        "CREATE TABLE word_characters (word_id INTEGER NOT NULL, ordinal INTEGER NOT NULL, character_id INTEGER NOT NULL, PRIMARY KEY(word_id, ordinal))"
    )
    connection.execute(
        "CREATE TABLE definitions (id INTEGER PRIMARY KEY, origin_word_id INTEGER NOT NULL, part_of_speech TEXT NOT NULL, ordinal INTEGER NOT NULL, sense_id TEXT NOT NULL, synset_id TEXT NOT NULL, definition_index INTEGER NOT NULL, text TEXT NOT NULL, previous_definition_id INTEGER)"
    )
    connection.execute(
        "CREATE TABLE definition_components (definition_id INTEGER NOT NULL, ordinal INTEGER NOT NULL, kind TEXT NOT NULL, word_id INTEGER, character_id INTEGER, start_offset INTEGER NOT NULL, end_offset INTEGER NOT NULL, PRIMARY KEY(definition_id, ordinal))"
    )
    connection.execute(
        "CREATE TABLE semantic_evidence (id INTEGER PRIMARY KEY, definition_id INTEGER NOT NULL, source_ordinal INTEGER NOT NULL, channel TEXT NOT NULL, relation TEXT NOT NULL, target_word_id INTEGER NOT NULL, target_ref TEXT NOT NULL)"
    )
    connection.executemany(
        "INSERT INTO characters(id, scalar, public_position) VALUES(?, ?, ?)",
        [(1, "a", 0), (2, "b", 1), (3, " ", None)],
    )
    connection.executemany(
        "INSERT INTO words(id, surface) VALUES(?, ?)",
        [(10, "ab"), (11, "bb")],
    )
    connection.executemany(
        "INSERT INTO word_characters(word_id, ordinal, character_id) VALUES(?, ?, ?)",
        [(10, 1, 1), (10, 2, 2), (11, 1, 2), (11, 2, 2)],
    )
    connection.executemany(
        "INSERT INTO definitions(id, origin_word_id, part_of_speech, ordinal, sense_id, synset_id, definition_index, text, previous_definition_id) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (100, 10, "n", 0, "s-100", "syn-100", 0, "bb ", None),
            (101, 11, "n", 0, "s-101", "syn-101", 0, "ab", None),
        ],
    )
    connection.executemany(
        "INSERT INTO definition_components(definition_id, ordinal, kind, word_id, character_id, start_offset, end_offset) VALUES(?, ?, ?, ?, ?, ?, ?)",
        [
            (100, 1, "word", 11, None, 0, 2),
            (100, 2, "whitespace", None, 3, 2, 3),
            (101, 1, "word", 10, None, 0, 2),
        ],
    )
    connection.executemany(
        "INSERT INTO semantic_evidence(id, definition_id, source_ordinal, channel, relation, target_word_id, target_ref) VALUES(?, ?, ?, ?, ?, ?, ?)",
        [
            (1, 100, 0, "semantic", "example:rel", 10, "ref-10"),
            (2, 100, 0, "semantic", "example:rel", 11, "ref-11"),
        ],
    )
    connection.commit()
    connection.close()
    return db_path, manifest_path


def _census(result) -> dict[str, int]:
    return {kind: rows for kind, _, rows in result.census}


def test_census_counts_every_constructed_relation(tmp_path: Path) -> None:
    db_path, manifest_path = _make_construct(tmp_path)
    result = build_relationship_census(db_path, manifest_path)

    counts = _census(result)
    assert counts["character_in_word"] == 4
    assert counts["word_origin_definition"] == 2
    assert counts["definition_to_word_component"] == 2
    assert counts["definition_to_character_component"] == 1
    assert counts["definition_chain_previous"] == 0
    assert counts["semantic_evidence_target"] == 2
    assert counts["word_to_words_in_definitions"] == 2
    assert counts["characters_in_word_to_characters_in_definitions"] == 4
    assert counts["character_cooccurrence_within_word"] == 2


def test_character_scale_participation_is_exact(tmp_path: Path) -> None:
    db_path, manifest_path = _make_construct(tmp_path)
    result = build_relationship_census(db_path, manifest_path)

    participation = {
        row["scalar"]: row for row in result.character_participation
    }
    assert participation["a"]["words_containing"] == 1
    assert participation["a"]["definitions_containing"] == 1
    assert participation["a"]["semantic_targets_containing"] == 1
    assert participation["b"]["words_containing"] == 2
    assert participation["b"]["definitions_containing"] == 2
    assert participation["b"]["semantic_targets_containing"] == 2
    assert participation[" "]["words_containing"] == 0
    assert participation[" "]["definitions_containing"] == 1
    assert participation[" "]["semantic_targets_containing"] == 0


def test_sizable_streams_are_determinable_not_stored(tmp_path: Path) -> None:
    db_path, manifest_path = _make_construct(tmp_path)
    result = build_relationship_census(db_path, manifest_path)

    for record in result.determinable_not_stored.values():
        assert record["stored"] is False

    word_rows = {
        row["word_id"]: row for row in iter_word_participation(db_path)
    }
    assert word_rows[10]["character_count"] == 2
    assert word_rows[10]["definitions_originated"] == 1
    assert word_rows[10]["definitions_containing"] == 1
    assert word_rows[10]["semantic_targets"] == 1
    assert word_rows[11]["character_count"] == 2
    assert word_rows[11]["definitions_originated"] == 1
    assert word_rows[11]["definitions_containing"] == 1
    assert word_rows[11]["semantic_targets"] == 1

    pair_rows = {
        (row["a_character_id"], row["b_character_id"]): row["count"]
        for row in iter_character_cooccurrence(db_path)
    }
    assert pair_rows[(1, 2)] == 1
    assert pair_rows[(2, 2)] == 1


def test_provenance_and_receipt_are_recorded(tmp_path: Path) -> None:
    db_path, manifest_path = _make_construct(tmp_path)
    result = build_relationship_census(db_path, manifest_path)

    assert result.schema == SCHEMA
    assert result.version == VERSION
    assert result.corpus["commit"] == "dc343f2683279ecbb13fab4e2fd778d7b162d287"
    assert result.builder["construct_receipt_sha256"] == "receipt-123"
    assert result.builder["construct_db_sha256"] == sha256(db_path.read_bytes()).hexdigest()
    assert len(result.receipt_sha256) == 64

    again = build_relationship_census(db_path, manifest_path)
    assert again.receipt_sha256 == result.receipt_sha256
    assert again.receipt_bytes() == result.receipt_bytes()


def test_stays_outside_the_construct(tmp_path: Path) -> None:
    db_path, manifest_path = _make_construct(tmp_path)
    before = db_path.read_bytes()
    out_dir = tmp_path / "relationships"

    result = run(db_path, manifest_path, out_dir)

    assert db_path.read_bytes() == before
    written = json.loads(
        (out_dir / "gonol-relationships.json").read_text(encoding="utf-8")
    )
    assert written["schema"] == SCHEMA
    assert written["receipt_sha256"] == result.receipt_sha256
    markdown = (out_dir / "gonol-relationships.md").read_text(encoding="utf-8")
    assert "Relationship census" in markdown


def test_fails_closed_on_wrong_construct_schema(tmp_path: Path) -> None:
    db_path, manifest_path = _make_construct(tmp_path)
    bad_manifest = _manifest()
    bad_manifest["schema"] = "english-gonol.something-else"
    bad_path = tmp_path / "bad-manifest.json"
    bad_path.write_text(json.dumps(bad_manifest), encoding="utf-8")

    with pytest.raises(GonolRelationshipError):
        build_relationship_census(db_path, bad_path)
