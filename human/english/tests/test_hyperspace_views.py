# === CHECKS ===
# id: check_views_are_four_plus_synthesis
#   proves: views_are_four_plus_synthesis
#   call: self::test_views_are_four_plus_synthesis
#   requires: python3, git
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_views_adjudication_counts_are_exact
#   proves: views_adjudication_counts_are_exact
#   call: self::test_adjudication_counts_are_exact
#   requires: python3, git
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_synthesis_is_first_class_and_replayable
#   proves: synthesis_is_first_class_and_replayable
#   call: self::test_synthesis_is_first_class_and_replayable
#   requires: python3, git
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_views_do_not_select
#   proves: views_do_not_select
#   call: self::test_views_do_not_select
#   requires: python3, git
#   timeout: 30
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from english_gonol.hyperspace_views import run_view_adjudication, word_views

UCNS_SOURCE_ROOT = Path(os.environ.get("UCNS_SOURCE_ROOT", "/tmp/ucns-motion"))


def _fixture_state(tmp_path: Path) -> Path:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    db = sqlite3.connect(state_dir / "construct.db")
    db.executescript(
        """
        CREATE TABLE characters (id INTEGER PRIMARY KEY, scalar TEXT NOT NULL UNIQUE, public_position INTEGER);
        CREATE TABLE words (id INTEGER PRIMARY KEY, surface TEXT NOT NULL UNIQUE);
        CREATE TABLE word_characters (
            word_id INTEGER NOT NULL REFERENCES words(id),
            ordinal INTEGER NOT NULL,
            character_id INTEGER NOT NULL REFERENCES characters(id),
            PRIMARY KEY (word_id, ordinal)
        ) WITHOUT ROWID;
        CREATE TABLE definitions (
            id INTEGER PRIMARY KEY,
            origin_word_id INTEGER NOT NULL REFERENCES words(id),
            part_of_speech TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            sense_id TEXT NOT NULL,
            synset_id TEXT NOT NULL,
            definition_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            previous_definition_id INTEGER REFERENCES definitions(id),
            UNIQUE (origin_word_id, ordinal)
        );
        CREATE TABLE definition_components (
            id INTEGER PRIMARY KEY,
            definition_id INTEGER NOT NULL REFERENCES definitions(id),
            ordinal INTEGER NOT NULL,
            kind TEXT NOT NULL,
            word_id INTEGER REFERENCES words(id),
            character_id INTEGER REFERENCES characters(id),
            start_offset INTEGER NOT NULL,
            end_offset INTEGER NOT NULL
        );
        CREATE TABLE semantic_evidence (
            id INTEGER PRIMARY KEY,
            definition_id INTEGER NOT NULL REFERENCES definitions(id),
            source_ordinal INTEGER NOT NULL,
            channel TEXT NOT NULL,
            relation TEXT NOT NULL,
            target_word_id INTEGER NOT NULL REFERENCES words(id),
            target_ref TEXT NOT NULL
        );
        """
    )
    db.execute("INSERT INTO characters VALUES (1, 'a', 0)")
    db.execute("INSERT INTO characters VALUES (2, 'b', 1)")
    db.executemany(
        "INSERT INTO words VALUES (?, ?)",
        [(1, "ab"), (2, "a"), (3, "b")],
    )
    db.executemany(
        "INSERT INTO word_characters VALUES (?, ?, ?)",
        [(1, 0, 1), (1, 1, 2), (2, 0, 1), (3, 0, 2)],
    )
    db.executemany(
        "INSERT INTO definitions VALUES (?, 1, 'noun', ?, 's', 'syn', ?, 'x', NULL)",
        [(1, 1, 1), (2, 2, 2)],
    )
    db.executemany(
        "INSERT INTO definition_components (id, definition_id, ordinal, kind, word_id, character_id, start_offset, end_offset) VALUES (?, ?, ?, 'word', ?, NULL, 0, 1)",
        [(1, 1, 0, 2), (2, 2, 0, 3)],
    )
    db.commit()
    db.close()
    return state_dir


def test_views_are_four_plus_synthesis(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    db = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    record = word_views(db, 1, UCNS_SOURCE_ROOT)
    db.close()
    assert set(record["views"]) == {
        "view1_definition_inner_product_density",
        "view2_word_axis_angle",
        "view3_provenance_interval_lift",
        "view4_canonical_witness_lift",
    }
    assert len(record["synthesis"]) == 3
    assert record["synthesis_composition"] == "views one, two, and three together"
    assert set(record["views"]["view2_word_axis_angle"]) == {
        "glyph_walk",
        "definition_walk",
    }
    assert record["views"]["view4_canonical_witness_lift"]["derived"] is True
    assert record["views"]["view3_provenance_interval_lift"]["deck"] == 0
    assert record["views"]["view4_canonical_witness_lift"]["lift"] == 157 + record["views"]["view4_canonical_witness_lift"]["residue"]


def test_adjudication_counts_are_exact(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    report = run_view_adjudication(state_dir, UCNS_SOURCE_ROOT)
    assert report["word_count"] == 3
    assert set(report["distinct_values"]) == {
        "view1_definition_inner_product_density",
        "view2_word_axis_angle",
        "view3_provenance_interval_lift",
        "synthesis",
    }
    assert report["view4_canonical_witness_lift"]["derived"] is True
    for name, distinct in report["distinct_values"].items():
        assert distinct <= report["word_count"]


def test_views_do_not_select(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    report = run_view_adjudication(state_dir, UCNS_SOURCE_ROOT)
    assert "ranking_by_distinctness" in report
    assert "select" not in report or report.get("selected") is None
    assert "view four reduces to derivation" in report["hmmm"]
    again = run_view_adjudication(state_dir, UCNS_SOURCE_ROOT)
    assert again["receipt_sha256"] == report["receipt_sha256"]


def test_synthesis_is_first_class_and_replayable(tmp_path: Path) -> None:
    from english_gonol.hyperspace_views import (
        build_synthesis_record,
        synthesis_corpus_receipt,
        verify_synthesis_replay,
    )
    import json

    state_dir = _fixture_state(tmp_path)
    db = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    record = build_synthesis_record(db, 1, UCNS_SOURCE_ROOT)
    db.close()
    assert record.word_id == 1
    assert record.surface == "ab"
    assert "view1" in record.as_dict() and "view2" in record.as_dict()

    report = synthesis_corpus_receipt(state_dir, UCNS_SOURCE_ROOT)
    data = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    replayed = verify_synthesis_replay(data, state_dir, UCNS_SOURCE_ROOT)
    assert replayed["receipt_sha256"] == report["receipt_sha256"]
