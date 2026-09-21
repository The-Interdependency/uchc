# === CHECKS ===
# id: check_hyperspace_glyph_carrier_and_axis_roles_are_distinct
#   proves: hyperspace_glyph_carrier_and_axis_roles_are_distinct
#   call: self::test_glyph_carrier_and_axis_roles_are_distinct
#   requires: python3
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_hyperspace_promotion_is_lossless
#   proves: hyperspace_promotion_is_lossless
#   call: self::test_promotion_is_lossless
#   requires: python3
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_hyperspace_orthogonality_is_declared_per_origin
#   proves: hyperspace_orthogonality_is_declared_per_origin
#   call: self::test_orthogonality_is_declared_per_origin
#   requires: python3
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_hyperspace_attachment_is_construction_derived
#   proves: hyperspace_attachment_is_construction_derived
#   call: self::test_attachment_is_construction_derived
#   requires: python3
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_hyperspace_fails_closed
#   proves: hyperspace_fails_closed
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

from english_gonol.hyperspace_construct import (
    HyperspaceError,
    attach_definition_frame,
    attach_word_origin,
    axes_orthogonal,
    compose_definition,
    compose_word,
    glyph_inventory,
    hyperspace_receipt,
    promote_definition,
    promote_glyph,
    promote_word,
    recover_definition,
    recover_glyph,
    recover_word,
    verify_hyperspace_replay,
)


def _fixture_state(tmp_path: Path) -> Path:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    db = sqlite3.connect(state_dir / "construct.db")
    db.executescript(
        """
        CREATE TABLE characters (
            id INTEGER PRIMARY KEY,
            scalar TEXT NOT NULL UNIQUE,
            public_position INTEGER
        );
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
    db.execute("INSERT INTO characters VALUES (3, '½', NULL)")
    db.execute("INSERT INTO words VALUES (1, 'ab')")
    db.execute("INSERT INTO words VALUES (2, 'a')")
    db.executemany(
        "INSERT INTO word_characters VALUES (?, ?, ?)",
        [(1, 0, 1), (1, 1, 2), (2, 0, 1)],
    )
    db.execute(
        "INSERT INTO definitions VALUES (1, 1, 'noun', 1, 's1', 'syn1', 1, 'a', NULL)"
    )
    db.execute(
        "INSERT INTO definitions VALUES (2, 2, 'noun', 1, 's2', 'syn2', 1, 'ab', NULL)"
    )
    db.executemany(
        "INSERT INTO definition_components (id, definition_id, ordinal, kind, word_id, character_id, start_offset, end_offset) VALUES (?, ?, ?, 'word', ?, NULL, 0, 1)",
        [(1, 1, 0, 2), (2, 2, 0, 1)],
    )
    db.commit()
    db.close()
    return state_dir


def test_glyph_carrier_and_axis_roles_are_distinct(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    db = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    inventory = glyph_inventory(db)
    db.close()
    assert inventory["a"].carrier_position == 0
    assert inventory["a"].construction_kind == "carrier"
    assert "carrier_position" in inventory["a"].as_dict()
    assert "axis_index" in inventory["a"].as_dict()
    assert inventory["½"].carrier_position is None
    assert inventory["½"].construction_kind in {"encoded-name", "encoded-codepoint"}
    # carrier position and axis participation are recorded separately
    assert "carrier_position" in inventory["a"].as_dict()
    assert "axis_index" in inventory["a"].as_dict()


def test_promotion_is_lossless(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    db = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    inventory = glyph_inventory(db)
    glyph, axis = promote_glyph(db, inventory, "½")
    assert recover_glyph(db, inventory, "½") == glyph
    word, word_axis = promote_word(db, 1)
    assert recover_word(db, 1) == word
    assert word_axis == word.axis_index
    definition, def_axis = promote_definition(db, 1)
    assert recover_definition(db, 1) == definition
    assert def_axis == definition.axis_index
    db.close()


def test_orthogonality_is_declared_per_origin(tmp_path: Path) -> None:
    assert axes_orthogonal("O_G", 0, 1) is True
    assert axes_orthogonal("O_W", 7, 7) is False
    assert axes_orthogonal("O_D", 3, 4) is True
    with pytest.raises(HyperspaceError):
        axes_orthogonal("O_X", 0, 1)


def test_attachment_is_construction_derived(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    db = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    word, _axis = promote_word(db, 1)
    db.close()
    word_attachment = attach_word_origin(word)
    frame_attachment = attach_definition_frame(word)
    assert word_attachment["attachment_point_q_w"] == word.axis_index
    assert frame_attachment["q_w"] == word.axis_index
    assert "admission order" in word_attachment["derivation"]


def test_composition_and_replay_fail_closed(tmp_path: Path) -> None:
    state_dir = _fixture_state(tmp_path)
    db = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    assert compose_word(db, 1) == (1, 2)
    assert compose_definition(db, 1) == (("word", 2),)
    assert compose_definition(db, 2) == (("word", 1),)
    db.close()

    report = hyperspace_receipt(state_dir)
    assert report["glyph_axis_count"] == 3
    assert report["word_axis_count"] == 2
    assert report["definition_axis_count"] == 2
    data = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    replayed = verify_hyperspace_replay(data, state_dir)
    assert replayed["receipt_sha256"] == report["receipt_sha256"]

    tampered = bytearray(data)
    tampered[40] ^= 0x01
    with pytest.raises(HyperspaceError):
        verify_hyperspace_replay(bytes(tampered), state_dir)

    with pytest.raises(HyperspaceError):
        hyperspace_receipt(tmp_path / "missing")
