# === CHECKS ===
# id: check_python_construct_acceptance_gates
#   proves: python_construct_one_shared_identity_per_glyph, python_construct_controls_are_constitutive, python_construct_newlines_remain_source_distinct, python_construct_off_carrier_is_hmmm_not_invented
#   call: self::test_acceptance_gates
#   requires: python3
#   timeout: 60
#   mutates: none
#   cleanup: none
#
# id: check_python_construct_replay_fails_closed_on_tamper
#   proves: python_construct_replay_fails_closed_on_tamper
#   call: self::test_tamper_fails_replay
#   requires: python3
#   timeout: 60
#   mutates: none
#   cleanup: none
#
# id: check_python_construct_tokens_verify_never_substitute
#   proves: python_construct_tokens_verify_never_substitute
#   call: self::test_tokens_and_ast_verify_never_substitute
#   requires: python3
#   timeout: 60
#   mutates: none
#   cleanup: none
#
# id: check_python_construct_corpus_completes_within_preflight
#   proves: python_construct_replay_fails_closed_on_tamper
#   call: self::test_declared_corpus_completes_within_preflight
#   requires: python3
#   timeout: 60
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from python_gonol import (
    PythonGonolConstructionError,
    affixiate_python_bytes,
    affixiate_python_source,
    reconstruct_source,
    verify_construct,
)

UCNS_SOURCE_ROOT = os.environ.get(
    "UCNS_SOURCE_ROOT",
    str(Path.home() / "src" / "ucns"),
)


def _build(tmp_path: Path, source: str, source_id: str = "example.py"):
    state_dir = tmp_path / f"construct-{source_id}"
    result = affixiate_python_source(
        source,
        source_id=source_id,
        ucns_source_root=UCNS_SOURCE_ROOT,
        state_dir=state_dir,
    )
    return state_dir, result


def _controls(state_dir: Path) -> list[tuple[int, int, int, int | None]]:
    connection = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    try:
        return list(
            connection.execute(
                "SELECT occurrence_id, control_identity_id, start_column, spaces_to_next_stop "
                "FROM controls ORDER BY id"
            )
        )
    finally:
        connection.close()


def _newlines(state_dir: Path) -> list[tuple[str, list[int]]]:
    import json

    connection = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    try:
        return [
            (kind, json.loads(ids))
            for kind, ids in connection.execute("SELECT kind, occurrence_ids FROM newlines ORDER BY id")
        ]
    finally:
        connection.close()


def test_acceptance_gates(tmp_path: Path) -> None:
    # x=1\n produces no not-on-pinned-carrier and verifies.
    state_dir, result = _build(tmp_path, "x=1\n")
    assert result.not_on_pinned_carrier == ()
    assert verify_construct(state_dir, UCNS_SOURCE_ROOT) == result.receipt_sha256

    # LF replays as exact U+000A and is a source-distinct LF newline.
    assert reconstruct_source(state_dir) == "x=1\n"
    assert _newlines(state_dir) == [("LF", [4])]

    # Shared identity: x, =, 1, \n share character rows; x occurs once.
    connection = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    try:
        scalar_rows = list(connection.execute("SELECT scalar, character_id FROM occurrences ORDER BY ordinal"))
        character_count = connection.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
    finally:
        connection.close()
    assert character_count == 157  # every pinned glyph has one shared identity
    # x has one shared character identity.
    x_ids = {character_id for scalar, character_id in scalar_rows if scalar == "x"}
    assert len(x_ids) == 1

    # TAB preserves U+0009 and expands correctly at every starting column.
    tab_source = "\t\tx"
    state_dir2, result2 = _build(tmp_path, tab_source, source_id="tabs.py")
    assert reconstruct_source(state_dir2) == "\t\tx"
    rows = _controls(state_dir2)
    assert len(rows) == 2
    assert rows[0][2] == 1 and rows[0][3] == 7  # column 1 -> 7 spaces
    assert rows[1][2] == 2 and rows[1][3] == 6  # column 2 -> 6 spaces

    # LF, CR, and CR+LF remain source-distinct.
    mixed = "a\nb\r\nc\rd"
    state_dir3, _result3 = _build(tmp_path, mixed, source_id="newlines.py")
    assert reconstruct_source(state_dir3) == mixed
    kinds = [kind for kind, _ids in _newlines(state_dir3)]
    assert kinds == ["LF", "CRLF", "CR"]
    assert _newlines(state_dir3)[1] == ("CRLF", [4, 5])


def test_tamper_fails_replay(tmp_path: Path) -> None:
    state_dir, _result = _build(tmp_path, "x=1\n")
    verify_construct(state_dir, UCNS_SOURCE_ROOT)

    connection = sqlite3.connect(state_dir / "construct.db")
    try:
        connection.execute("UPDATE occurrences SET column = column + 1 WHERE ordinal = 0")
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(PythonGonolConstructionError):
        verify_construct(state_dir, UCNS_SOURCE_ROOT)


def test_tokens_and_ast_verify_never_substitute(tmp_path: Path) -> None:
    state_dir, result = _build(tmp_path, "def f():\n    return 1\n")
    assert result.tokenize_ok is True
    assert result.ast_ok is True
    assert verify_construct(state_dir, UCNS_SOURCE_ROOT) == result.receipt_sha256

    broken_dir, broken = _build(tmp_path, "def f(:\n", source_id="broken.py")
    assert broken.tokenize_ok is False or broken.ast_ok is False
    assert verify_construct(broken_dir, UCNS_SOURCE_ROOT) == broken.receipt_sha256


def test_declared_corpus_completes_within_preflight(tmp_path: Path) -> None:
    corpus = {
        "one.py": "x=1\n",
        "tabs.py": "if True:\n\tpass\n",
        "newlines.py": "a\r\nb\rc\n",
        "surface.py": (
            "import ast\n"
            "def f(x: int = 3) -> str:\n"
            "    return f'{x!r}'\n"
            "class A:\n"
            "    def __init__(self):\n"
            "        self.items = [1, 2, 3]\n"
        ),
    }
    for source_id, source in corpus.items():
        state_dir = tmp_path / source_id
        result = affixiate_python_source(
            source,
            source_id=source_id,
            ucns_source_root=UCNS_SOURCE_ROOT,
            state_dir=state_dir,
        )
        db_size = (state_dir / "construct.db").stat().st_size
        assert db_size <= result.preflight_storage_bytes
        assert verify_construct(state_dir, UCNS_SOURCE_ROOT) == result.receipt_sha256


def test_off_carrier_unicode_is_hmmm_not_invented(tmp_path: Path) -> None:
    state_dir, result = _build(tmp_path, "a\u20acb", source_id="euro.py")
    assert "\u20ac" in result.not_on_pinned_carrier
    assert reconstruct_source(state_dir) == "a\u20acb"
    connection = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT character_id, control_kind FROM occurrences WHERE ordinal = 1"
        ).fetchone()
    finally:
        connection.close()
    assert row == (None, None)
    assert verify_construct(state_dir, UCNS_SOURCE_ROOT) == result.receipt_sha256
