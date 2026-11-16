from __future__ import annotations

import sqlite3
from pathlib import Path

from english_gonol.hyperspace_views import run_view_adjudication, word_views


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


def test_view_measures_stored_definition_pairs(tmp_path: Path) -> None:
    state = _fixture_state(tmp_path)
    with sqlite3.connect(state / "construct.db") as db:
        first = word_views(db, 1)
        assert first["views"] == {"view1_definition_inner_product_density": {
            "definition_count": 2, "pair_count": 1, "orthogonal_pair_count": 1, "shared_sum": 0,
        }}
        assert first == word_views(db, 1)
        assert word_views(db, 2)["views"]["view1_definition_inner_product_density"] is None
    report = run_view_adjudication(state)
    assert report["word_count"] == 3
    assert report["distinct_values"] == {"view1_definition_inner_product_density": 2}
    assert report["collisions"] == {"view1_definition_inner_product_density": 1}
    assert run_view_adjudication(state, limit=1)["word_count"] == 1
