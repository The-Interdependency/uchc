# === CHECKS ===
# id: check_describing_graph_is_external
#   proves: describing_graph_is_external
#   call: self::test_describing_graph_is_external
#   requires: python3
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_describing_graph_channels_are_construction_derived
#   proves: describing_graph_channels_are_construction_derived
#   call: self::test_channels_are_construction_derived
#   requires: python3
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_describing_graph_fails_closed
#   proves: describing_graph_fails_closed
#   call: self::test_fails_closed
#   requires: python3
#   timeout: 30
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from english_gonol.describing_graph import (
    DescribingGraphError,
    describe_word,
    describing_graph_receipt,
    verify_describing_graph_replay,
)


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


def test_describing_graph_is_external(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    db = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    record = describe_word(db, 1)
    db.close()
    assert set(record) >= {"x", "y", "z"}
    assert "shares no origin" in record["origin"]


def test_channels_are_construction_derived(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    db = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    record = describe_word(db, 1)
    db.close()
    assert record["x"] == 1 % 157
    assert record["y"] == 2 % 157
    assert record["z"] == 2 % 157


def test_fails_closed(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    report = describing_graph_receipt(state_dir)
    assert report["external"] is True
    data = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    replayed = verify_describing_graph_replay(data, state_dir)
    assert replayed["receipt_sha256"] == report["receipt_sha256"]

    tampered = bytearray(data)
    tampered[30] ^= 0x01
    with pytest.raises(DescribingGraphError):
        verify_describing_graph_replay(bytes(tampered), state_dir)

    with pytest.raises(DescribingGraphError):
        describing_graph_receipt(tmp_path / "missing")
