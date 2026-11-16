from __future__ import annotations

import sqlite3
from pathlib import Path

from english_gonol.hyperspace_geometry import (
    definition_inner_product,
    run_hyperspace_geometry_controls,
)


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
        """
    )
    db.execute("INSERT INTO characters VALUES (1, 'a', 0)")
    db.execute("INSERT INTO characters VALUES (2, 'b', 1)")
    db.execute("INSERT INTO characters VALUES (3, 'c', 2)")
    db.executemany(
        "INSERT INTO words VALUES (?, ?)",
        [(1, "abc"), (2, "a"), (3, "b"), (4, "c")],
    )
    db.executemany(
        "INSERT INTO word_characters VALUES (?, ?, ?)",
        [(1, 0, 1), (1, 1, 2), (1, 2, 3), (2, 0, 1), (3, 0, 2), (4, 0, 3)],
    )
    db.executemany(
        "INSERT INTO definitions VALUES (?, 1, 'noun', ?, 's', 'syn', ?, 'x', NULL)",
        [(1, 1, 1), (2, 2, 2), (3, 3, 3)],
    )
    # def 1: words 2 and 3 -> {a, b}; def 2: word 4 -> {c}; def 3: words 2 and 4 -> {a, c}
    db.executemany(
        "INSERT INTO definition_components (id, definition_id, ordinal, kind, word_id, character_id, start_offset, end_offset) VALUES (?, ?, ?, 'word', ?, NULL, 0, 1)",
        [(1, 1, 0, 2), (2, 1, 1, 3), (3, 2, 0, 4), (4, 3, 0, 2), (5, 3, 1, 4)],
    )
    db.commit()
    db.close()
    return state_dir


def test_definition_inner_product_is_constructed_not_statistical(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    db = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    self_product = definition_inner_product(db, 1, 1, 1)
    assert self_product["inner_product"] == self_product["norm_first"] == 2
    disjoint = definition_inner_product(db, 1, 1, 2)
    assert disjoint["orthogonal"] is True and disjoint["inner_product"] == 0
    shared = definition_inner_product(db, 1, 1, 3)
    assert shared["orthogonal"] is False and shared["inner_product"] == 1
    db.close()


def test_candidates_are_replayable(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    report = run_hyperspace_geometry_controls(state_dir)
    assert report["survivors"] == ["definition-inner-product"]
    assert report["selected"] == []
    again = run_hyperspace_geometry_controls(state_dir)
    assert again["receipt_sha256"] == report["receipt_sha256"]
