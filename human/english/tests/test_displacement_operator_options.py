# === CHECKS ===
# id: check_channel_options_are_built
#   proves: channel_options_are_built
#   call: self::test_channel_options_are_built
#   requires: python3, git
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_channel_option_selection_preserves_identity
#   proves: channel_option_selection_preserves_identity
#   call: self::test_selection_preserves_identity
#   requires: python3, git
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_channel_option_selection_prefers_distinctness
#   proves: channel_option_selection_prefers_distinctness
#   call: self::test_selection_prefers_distinctness
#   requires: python3, git
#   timeout: 30
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from english_gonol.displacement_operator_options import (
    channel_option_a,
    channel_option_b,
    channel_option_c,
    run_channel_option_adjudication,
)

UCNS_SOURCE_ROOT = Path(os.environ.get("UCNS_SOURCE_ROOT", "/tmp/ucns-lift"))


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
    db.executemany("INSERT INTO words VALUES (?, ?)", [(1, "ab"), (2, "a"), (3, "b")])
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


def test_channel_options_are_built(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    db = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    assert channel_option_a(db, 1)[0] == 1
    assert channel_option_b(db, 1, UCNS_SOURCE_ROOT)[0] == 1
    assert channel_option_c(db, 1)[0] == 1
    db.close()


def test_selection_preserves_identity(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    report = run_channel_option_adjudication(state_dir, UCNS_SOURCE_ROOT)
    assert report["word_count"] == 3
    for option in ("a", "b", "c"):
        assert report["options"][option]["identity_preserved"] is True
    assert report["selected"] in ("a", "b", "c")


def test_selection_prefers_distinctness(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    report = run_channel_option_adjudication(state_dir, UCNS_SOURCE_ROOT)
    selected = report["selected"]
    assert selected is not None
    assert report["options"][selected]["distinct_receipts"] == max(
        stats["distinct_receipts"] for stats in report["options"].values()
    )
    assert "preserving the identity" in report["hmmm"]
