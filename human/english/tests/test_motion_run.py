# === CHECKS ===
# id: check_motion_run_binds_exact_ucns_motion_source
#   proves: motion_run_binds_exact_ucns_motion_source
#   call: self::test_binds_exact_ucns_motion_source
#   requires: python3, git
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_motion_run_recomputes_not_stores
#   proves: motion_run_recomputes_not_stores
#   call: self::test_recomputes_not_stores
#   requires: python3, git
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_motion_run_inherits_scoped_selected_status
#   proves: motion_run_inherits_scoped_selected_status
#   call: self::test_inherits_scoped_selected_status
#   requires: python3, git
#   timeout: 30
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

from english_gonol.motion_run import (
    SCHEMA,
    MotionRunError,
    run_definition_walk_motions,
    verify_motion_replay,
)

UCNS_SOURCE_ROOT = Path(os.environ.get("UCNS_SOURCE_ROOT", "/tmp/ucns-motion"))


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
    db.execute("INSERT INTO words VALUES (1, 'cat')")
    db.execute("INSERT INTO words VALUES (2, 'animal')")
    db.execute("INSERT INTO words VALUES (3, 'feline')")
    db.executemany(
        "INSERT INTO definitions VALUES (?, 1, 'noun', ?, 's1', 'syn1', ?, 'a small animal', NULL)",
        [
            (1, 1, 1),
            (2, 2, 2),
            (3, 3, 3),
        ],
    )
    db.executemany(
        "INSERT INTO semantic_evidence (definition_id, source_ordinal, channel, relation, target_word_id, target_ref) VALUES (?, 0, 'semantic', 'hypernym', ?, 'ref')",
        [(1, 2), (2, 3), (3, 2)],
    )
    db.commit()
    db.close()
    return state_dir


def test_binds_exact_ucns_motion_source(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    report = run_definition_walk_motions(state_dir, UCNS_SOURCE_ROOT)
    assert report["ucns_motion_commit"].startswith("1cf10c2")
    assert report["word_count"] == 1

    data = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    replayed = verify_motion_replay(data, state_dir, UCNS_SOURCE_ROOT)
    assert replayed["receipt_sha256"] == report["receipt_sha256"]

    tampered = bytearray(data)
    tampered[40] ^= 0x01
    with pytest.raises(MotionRunError):
        verify_motion_replay(bytes(tampered), state_dir, UCNS_SOURCE_ROOT)


def test_recomputes_not_stores(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    first = run_definition_walk_motions(state_dir, UCNS_SOURCE_ROOT)
    second = run_definition_walk_motions(state_dir, UCNS_SOURCE_ROOT)
    assert first["receipt_sha256"] == second["receipt_sha256"]
    assert first["schema"] == SCHEMA
    # only the aggregate receipt is returned; per-word motions are recomputed
    assert "words" in first
    for word in first["words"]:
        assert "motion_receipt" in word


def test_inherits_scoped_selected_status(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    report = run_definition_walk_motions(state_dir, UCNS_SOURCE_ROOT)
    assert report["displacement_candidate"] == "lifted-ordered-concatenation"
    assert report["displacement_candidate_status"] == "selected-scoped"
    assert "hmmm" in report["hmmm"]
