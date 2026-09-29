# === CHECKS ===
# id: check_construct_tensor_has_all_modes
#   proves: construct_tensor_has_all_modes
#   call: self::test_has_all_modes
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_construct_tensor_holes_are_named
#   proves: construct_tensor_holes_are_named
#   call: self::test_holes_are_named
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_construct_tensor_tau_is_circle_plus_cover
#   proves: construct_tensor_tau_is_circle_plus_cover
#   call: self::test_tau_is_circle_plus_cover
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_construct_tensor_flattening_forbidden
#   proves: construct_tensor_flattening_forbidden
#   call: self::test_flattening_forbidden
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_construct_tensor_weights_share_modes
#   proves: construct_tensor_weights_share_modes
#   call: self::test_weights_share_modes
#   requires: python3
#   timeout: 30
#   mutates: none
#   cleanup: none
# === END CHECKS ===
from hashlib import sha256
import os
from pathlib import Path

import pytest

from english_gonol.construct_tensor import (
    MODES,
    TensorError,
    TensorRecord,
    TensorWeights,
    build_tensor,
    read_full_index_record,
    tensor_phone_card,
    write_full_index_record,
)
from english_gonol.full_construct_run import build_construct
from english_gonol.inference_input import EnglishConstruct
from english_gonol.language.source import LexemeRecord, SenseRecord, SynsetRecord, WordnetSnapshot

UCNS_SOURCE_ROOT = Path(os.environ.get("UCNS_SOURCE_ROOT", "/tmp/ucns-infer"))


@pytest.fixture
def artifact(tmp_path):
    snapshot = WordnetSnapshot(
        lexemes=(
            LexemeRecord("alpha", "n", (), (
                SenseRecord("s1", "one", (("also", ("s3",)),)),
                SenseRecord("s2", "two", (("also", ("missing",)),)),
            )),
            LexemeRecord("other", "n", (), (SenseRecord("s3", "three", ()),)),
        ),
        synsets=(
            SynsetRecord("one", "n", ("alpha",), ("alpha letter alpha.",), ()),
            SynsetRecord("two", "n", ("alpha",), ("other word",), ()),
            SynsetRecord("three", "n", ("other",), ("another word",), ()),
        ),
        source_tree_sha256="0" * 64,
        source_file_count=3,
    )
    path = tmp_path / "construct.db"
    result = build_construct(snapshot, db_path=path, public_position=lambda c: None)
    return path, sha256(path.read_bytes()).hexdigest(), result["receipt_sha256"]


def _open(artifact):
    path, digest, logical = artifact
    return EnglishConstruct(path, database_sha256=digest, logical_receipt=logical)


def test_has_all_modes(artifact, tmp_path):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:tensor").require_complete()
        tensor = build_tensor(frame, corpus, UCNS_SOURCE_ROOT)
        assert set(tensor.axes) == set(MODES)
        assert tensor.entries
        for entry in tensor.entries:
            assert {"g", "w", "d", "tau", "pi"} <= set(entry)
        record_path = write_full_index_record(tensor, tmp_path / "tensor.json")
        assert record_path.read_bytes() == tensor.bytes()


def test_holes_are_named(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("another word", source_id="fixture:holes").require_complete()
        alpha = corpus.word("alpha")
        tensor = build_tensor(frame, corpus, UCNS_SOURCE_ROOT,
                              extra_definition_ids=(alpha.definition_ids[0],))
        assert tensor.axis_holes["w"]
        hole_entries = [
            entry for entry in tensor.entries
            if isinstance(entry["w"], dict) and entry["w"].get("hole")
        ]
        assert hole_entries
        assert all("hole" in entry["w"] for entry in hole_entries)
        assert all("hole" in entry["g"] for entry in hole_entries)


def test_tau_is_circle_plus_cover(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:tau").require_complete()
        tensor = build_tensor(frame, corpus, UCNS_SOURCE_ROOT)
        tau_values = [entry["tau"] for entry in tensor.entries if not isinstance(entry["tau"], dict)]
        assert tau_values
        for tau in tau_values:
            assert isinstance(tau, list) and len(tau) == 3
            assert tau[2] in (-1, 1)
            assert -1.0 <= tau[0] <= 1.0 and -1.0 <= tau[1] <= 1.0


def test_flattening_forbidden(artifact, tmp_path):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:flat").require_complete()
        tensor = build_tensor(frame, corpus, UCNS_SOURCE_ROOT)
        data = tensor.bytes()
        assert b"axes" in data and b"entries" in data
        reloaded = read_full_index_record(data)
        assert reloaded.as_dict() == tensor.as_dict()
        card = tensor_phone_card(tensor)
        assert card["contracted"] is True and card["entry_count"] == len(tensor.entries)
        with pytest.raises(TensorError):
            read_full_index_record(b'{"schema":"wrong"}')
        assert "if you can delete an index" in tensor.hmmm


def test_weights_share_modes():
    weights = TensorWeights(factors={"g": [1, 2], "tau": [0.1, 0.2]})
    assert set(weights.factors) <= set(MODES)
    with pytest.raises(TensorError):
        TensorWeights(factors={"unnamed": [1, 2, 3]})
    with pytest.raises(TensorError):
        TensorWeights(factors={"probe": [1]})
