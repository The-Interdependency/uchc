# ratios: loc_comments=230:74 imports_exports=11:12 calls_definitions=104:15
# === CHECKS ===
# id: check_python_complete_constitutive_replay
#   proves: python_construct_replay_fails_closed_on_tamper
#   call: self::test_complete_replay_rejects_constitutive_tamper
#   requires: python3, pytest
#   mutates: filesystem
#   cleanup: pytest_tmp_path
#
# id: check_python_original_source_bytes
#   proves: python_construct_preserves_source_bytes
#   call: self::test_replay_preserves_original_bytes
#   requires: python3, pytest
#   mutates: filesystem
#   cleanup: pytest_tmp_path
#
# id: check_python_legacy_receipt_rejection
#   proves: python_construct_replay_fails_closed_on_tamper
#   call: self::test_replay_rejects_legacy_version
#   requires: python3, pytest
#   mutates: filesystem
#   cleanup: pytest_tmp_path
#
# id: check_python_tabs_match_python_expansion
#   proves: python_construct_controls_are_constitutive
#   call: self::test_tabs_match_python_expansion
#   requires: python3, pytest
#   mutates: filesystem
#   cleanup: pytest_tmp_path
#
# id: check_python_physical_source_addresses
#   proves: python_construct_physical_addresses
#   call: self::test_physical_source_addresses
#   requires: python3, pytest
#   mutates: filesystem
#   cleanup: pytest_tmp_path
#
# id: check_python_construct_acceptance_gates
#   proves: python_construct_one_shared_identity_per_glyph, python_construct_controls_are_constitutive, python_construct_newlines_remain_source_distinct, python_construct_unicode_identity
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
import json
from hashlib import sha256
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

UCNS_SOURCE_ROOT = os.environ.get("PYTHON_GONOL_UCNS_ROOT") or os.environ.get(
    "UCNS_SOURCE_ROOT", str(Path.home() / "src" / "ucns")
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
    # Every source occurrence, including LF, has a Unicode identity.
    state_dir, result = _build(tmp_path, "x=1\n")
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
    assert character_count == 158  # the Public Gonol inventory and LF
    assert scalar_rows == [(ch, ord(ch)) for ch in "x=1\n"]
    # x has one shared character identity.
    x_ids = {character_id for scalar, character_id in scalar_rows if scalar == "x"}
    assert len(x_ids) == 1

    # TAB preserves U+0009 and expands correctly at every starting column.
    tab_source = "\t\tx"
    state_dir2, result2 = _build(tmp_path, tab_source, source_id="tabs.py")
    assert reconstruct_source(state_dir2) == "\t\tx"
    rows = _controls(state_dir2)
    assert len(rows) == 2
    assert rows[0][2] == 1 and rows[0][3] == 8
    assert rows[1][2] == 2 and rows[1][3] == 8

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


def test_full_unicode_identities_are_shared_across_sources(tmp_path: Path) -> None:
    from fractions import Fraction

    source = "eëe\u0308🐍\0\ufeff\t\f\r\n\U0010ffffë"
    first, result = _build(tmp_path, source)
    second, _ = _build(tmp_path, source[::-1], "reversed.py")
    receipts = []
    for directory, text in ((first, source), (second, source[::-1])):
        with sqlite3.connect(directory / "construct.db") as db:
            rows = db.execute(
                "SELECT o.ordinal, c.id, c.scalar, c.utf32_be, c.utf8, c.public_position, "
                "c.turn_numerator, c.turn_denominator, c.glyph_receipt FROM occurrences o "
                "JOIN characters c ON o.character_id=c.id ORDER BY o.ordinal"
            ).fetchall()
        assert len(rows) == len(text)
        for i, identity, scalar, utf32, utf8, position, n, d, receipt in rows:
            assert (scalar, identity) == (text[i], ord(text[i]))
            assert (utf32, utf8) == (scalar.encode("utf-32-be"), scalar.encode("utf-8"))
            assert Fraction(n, d) == Fraction((identity - 32) % 0x110000, 0x110000)
            if scalar in "ë🐍\u0308\U0010ffff":
                assert position is None
            assert len(receipt) == 64
        receipts.append({row[2]: (row[1], row[-1]) for row in rows})
    assert receipts[0] == receipts[1]
    assert reconstruct_source(first) == source
    assert verify_construct(first, UCNS_SOURCE_ROOT) == result.receipt_sha256


@pytest.mark.parametrize("text", ["\ud800", "ok\udfff"])
def test_surrogates_rejected_before_publication(tmp_path: Path, text: str) -> None:
    with pytest.raises(PythonGonolConstructionError, match="surrogate"):
        _build(tmp_path, text)
    assert not list(tmp_path.rglob("construct.db"))


def test_overwrite_rebuilds_from_original_bytes(tmp_path: Path) -> None:
    state, old = _build(tmp_path, "x=1\n")
    raw = b"# coding: latin-1\r\n# \xeb\r\n"
    new = affixiate_python_bytes(raw, source_id="latin.py", ucns_source_root=UCNS_SOURCE_ROOT,
                                 state_dir=state, overwrite=True)
    assert verify_construct(state, UCNS_SOURCE_ROOT) == new.receipt_sha256 != old.receipt_sha256
    with sqlite3.connect(state / "construct.db") as db:
        assert db.execute("SELECT data FROM source_bytes").fetchone() == (raw,)
        assert db.execute("SELECT utf32_be FROM characters WHERE id=235").fetchone() == (b"\0\0\0\xeb",)


@pytest.mark.parametrize("prefix", [" " * n for n in range(16)] + [
    "\t", " \t", "\t ", "\f", "abc\f", "\t\f", "abc\f\f", "abc\r", "abc\r\n",
])
def test_tabs_match_python_expansion(tmp_path: Path, prefix: str) -> None:
    source = prefix + "\tx\n"
    state_dir, result = _build(tmp_path, source)
    expected = [
        len(source[:i + 1].expandtabs(8)) - len(source[:i].expandtabs(8))
        for i, scalar in enumerate(source) if scalar == "\t"
    ]
    assert [row[3] for row in _controls(state_dir) if source[row[0] - 1] == "\t"] == expected
    assert reconstruct_source(state_dir) == source
    assert verify_construct(state_dir, UCNS_SOURCE_ROOT) == result.receipt_sha256


@pytest.mark.parametrize("source,expected", [
    ("a\rb", [(1, 1), (1, 2), (2, 1)]),
    ("a\nb", [(1, 1), (1, 2), (2, 1)]),
    ("a\r\nb", [(1, 1), (1, 2), (1, 3), (2, 1)]),
    ("\r\rb", [(1, 1), (2, 1), (3, 1)]),
])
def test_physical_source_addresses(tmp_path: Path, source: str, expected: list) -> None:
    state_dir, result = _build(tmp_path, source)
    with sqlite3.connect(state_dir / "construct.db") as db:
        positions = list(db.execute("SELECT line, column FROM occurrences ORDER BY ordinal"))
    assert positions == expected
    assert reconstruct_source(state_dir) == source
    assert verify_construct(state_dir, UCNS_SOURCE_ROOT) == result.receipt_sha256


@pytest.mark.parametrize("statement", [
    "UPDATE control_identities SET member_ids='[]' WHERE kind='TAB'",
    "UPDATE characters SET public_position=900 WHERE scalar='Z'",
    "UPDATE characters SET utf32_be=x'00000000' WHERE scalar='x'",
    "UPDATE characters SET turn_numerator=999 WHERE scalar='x'",
    "UPDATE characters SET glyph_receipt='wrong' WHERE scalar='x'",
    "UPDATE occurrences SET character_id=120 WHERE scalar=char(9)",
    "UPDATE occurrences SET control_kind='TAB' WHERE scalar='x'",
    "UPDATE meta SET value='wrong' WHERE key='source_bytes_sha256'",
    "DELETE FROM occurrences",
    "CREATE VIEW forged_view AS SELECT * FROM occurrences",
    "CREATE TRIGGER forged_trigger AFTER INSERT ON occurrences BEGIN DELETE FROM occurrences; END",
    "CREATE INDEX forged_index ON occurrences(scalar)",
])
@pytest.mark.parametrize("rebind", [False, True])
def test_complete_replay_rejects_constitutive_tamper(tmp_path: Path, statement: str, rebind: bool) -> None:
    from python_gonol.construct import _logical_sha256
    state_dir, _ = _build(tmp_path, "\tx=1\n")
    manifest_path = state_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    with sqlite3.connect(state_dir / "construct.db") as db:
        db.execute(statement)
        if rebind:
            manifest["construct_sha256"] = _logical_sha256(db)
            manifest.pop("receipt_sha256")
            digest = sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            manifest["receipt_sha256"] = digest
            db.execute("UPDATE meta SET value=? WHERE key='receipt_sha256'", (digest,))
            manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(PythonGonolConstructionError):
        verify_construct(state_dir, UCNS_SOURCE_ROOT)


@pytest.mark.parametrize("raw", [b"", b"\xef\xbb\xbfx=1\r\n", b"# coding: latin-1\n# caf\xe9\n"])
def test_replay_preserves_original_bytes(tmp_path: Path, raw: bytes) -> None:
    state_dir = tmp_path / "raw"
    result = affixiate_python_bytes(raw, source_id="raw.py", state_dir=state_dir, ucns_source_root=UCNS_SOURCE_ROOT)
    with sqlite3.connect(state_dir / "construct.db") as db:
        assert db.execute("SELECT data FROM source_bytes").fetchall() == [(raw,)]
    assert verify_construct(state_dir, UCNS_SOURCE_ROOT) == result.receipt_sha256


@pytest.mark.parametrize("legacy", ["1.0.0", "2.0.0"])
def test_replay_rejects_legacy_version(tmp_path: Path, legacy: str) -> None:
    state_dir, _ = _build(tmp_path, "x=1\n")
    path = state_dir / "manifest.json"
    data = json.loads(path.read_text()); data["version"] = legacy
    path.write_text(json.dumps(data))
    with pytest.raises(PythonGonolConstructionError, match="version"):
        verify_construct(state_dir, UCNS_SOURCE_ROOT)
# ratios: loc_comments=230:74 imports_exports=11:12 calls_definitions=104:15
