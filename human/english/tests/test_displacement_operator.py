# === CHECKS ===
# id: check_displacement_operator_uses_selected_laws
#   proves: displacement_operator_uses_selected_laws
#   call: self::test_uses_selected_laws
#   requires: python3, git
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_displacement_operator_closes_inside_word_origin
#   proves: displacement_operator_closes_inside_word_origin
#   call: self::test_closes_inside_word_origin
#   requires: python3, git
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_displacement_operator_iteration_is_deck_translation
#   proves: displacement_operator_iteration_is_deck_translation
#   call: self::test_iteration_is_deck_translation
#   requires: python3, git
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_displacement_operator_fails_closed
#   proves: displacement_operator_fails_closed
#   call: self::test_fails_closed
#   requires: python3, git
#   timeout: 30
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from english_gonol.displacement_operator import (
    DisplacementOperatorError,
    apply_word_displacement,
    displacement_operator_receipt,
    run_displacement_operator_controls,
)

UCNS_SOURCE_ROOT = Path(os.environ.get("UCNS_SOURCE_ROOT", "/tmp/ucns-lift"))


def _fixture_state(tmp_path: Path) -> Path:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    db = sqlite3.connect(state_dir / "construct.db")
    db.executescript(
        """
        CREATE TABLE words (id INTEGER PRIMARY KEY, surface TEXT NOT NULL UNIQUE);
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
    db.executemany("INSERT INTO words VALUES (?, ?)", [(1, "a"), (2, "b")])
    db.executemany(
        "INSERT INTO definitions VALUES (?, 1, 'noun', ?, 's', 'syn', 1, 'x', NULL)",
        [(1, 1), (2, 2)],
    )
    db.execute(
        "INSERT INTO semantic_evidence (definition_id, source_ordinal, channel, relation, target_word_id, target_ref) VALUES (1, 0, 'semantic', 'hypernym', 2, 'ref')"
    )
    db.commit()
    db.close()
    return state_dir


def test_uses_selected_laws(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    db = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    record = apply_word_displacement(db, 1, UCNS_SOURCE_ROOT)
    db.close()
    assert record["channels"]["ordinal"] == 1
    assert record["channels"]["semantic"] == 2
    assert record["channels"]["context"] == 2
    assert record["lift"] % 157 == int(record["end_phase"].split("/")[0]) % 157


def test_closes_inside_word_origin(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    db = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    record = apply_word_displacement(db, 1, UCNS_SOURCE_ROOT)
    db.close()
    assert "O_W" in record["closure"]


def test_iteration_is_deck_translation(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    db = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    once = apply_word_displacement(db, 1, UCNS_SOURCE_ROOT, iterations=1)
    twice = apply_word_displacement(db, 1, UCNS_SOURCE_ROOT, iterations=2)
    db.close()
    assert twice["lift"] == once["lift"] + 157


def test_fails_closed(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    db = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    with pytest.raises(DisplacementOperatorError):
        apply_word_displacement(db, 1, UCNS_SOURCE_ROOT, iterations=-1)
    db.close()

    report = run_displacement_operator_controls(state_dir, UCNS_SOURCE_ROOT)
    assert report["ok"] is True
    receipt = displacement_operator_receipt(state_dir, UCNS_SOURCE_ROOT)
    assert receipt["word_count"] == 2

    with pytest.raises(DisplacementOperatorError):
        displacement_operator_receipt(tmp_path / "missing", UCNS_SOURCE_ROOT)
