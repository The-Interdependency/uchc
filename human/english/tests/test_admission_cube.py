# === CHECKS ===
# id: check_admission_cube_has_all_modes
#   proves: admission_cube_has_all_modes
#   call: self::test_has_all_modes
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_admission_cube_holes_are_named
#   proves: admission_cube_holes_are_named
#   call: self::test_holes_are_named
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_admission_cube_tau_is_circle_plus_cover
#   proves: admission_cube_tau_is_circle_plus_cover
#   call: self::test_tau_is_circle_plus_cover
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_admission_cube_flattening_forbidden
#   proves: admission_cube_flattening_forbidden
#   call: self::test_flattening_forbidden
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_admission_cube_weights_share_modes
#   proves: admission_cube_weights_share_modes
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

from english_gonol.admission_cube import (
    MODES,
    AdmissionCubeError,
    AdmissionCube,
    AdmissionWeights,
    build_admission_cube,
    read_full_index_record,
    admission_cube_phone_card,
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
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:cube").require_complete()
        cube = build_admission_cube(frame, corpus, UCNS_SOURCE_ROOT)
        assert set(cube.axes) == set(MODES)
        assert cube.entries
        for entry in cube.entries:
            assert {"g", "w", "d", "tau", "pi"} <= set(entry)
        record_path = write_full_index_record(cube, tmp_path / "cube.json")
        assert record_path.read_bytes() == cube.bytes()


def test_holes_are_named(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("another word", source_id="fixture:holes").require_complete()
        alpha = corpus.word("alpha")
        cube = build_admission_cube(frame, corpus, UCNS_SOURCE_ROOT,
                              extra_definition_ids=(alpha.definition_ids[0],))
        assert cube.axis_holes["w"]
        hole_entries = [
            entry for entry in cube.entries
            if isinstance(entry["w"], dict) and entry["w"].get("hole")
        ]
        assert hole_entries
        assert all("hole" in entry["w"] for entry in hole_entries)
        assert all("hole" in entry["g"] for entry in hole_entries)


def test_tau_is_circle_plus_cover(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:tau").require_complete()
        cube = build_admission_cube(frame, corpus, UCNS_SOURCE_ROOT)
        tau_values = [entry["tau"] for entry in cube.entries if not isinstance(entry["tau"], dict)]
        assert tau_values
        for tau in tau_values:
            assert isinstance(tau, list) and len(tau) == 3
            assert tau[2] in (-1, 1)
            assert -1.0 <= tau[0] <= 1.0 and -1.0 <= tau[1] <= 1.0


def test_flattening_forbidden(artifact, tmp_path):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:flat").require_complete()
        cube = build_admission_cube(frame, corpus, UCNS_SOURCE_ROOT)
        data = cube.bytes()
        assert b"axes" in data and b"entries" in data
        reloaded = read_full_index_record(data)
        assert reloaded.as_dict() == cube.as_dict()
        card = admission_cube_phone_card(cube)
        assert card["contracted"] is True and card["entry_count"] == len(cube.entries)
        with pytest.raises(AdmissionCubeError):
            read_full_index_record(b'{"schema":"wrong"}')
        assert "if you can delete an index" in cube.hmmm


def test_weights_share_modes():
    weights = AdmissionWeights(factors={"g": [1, 2], "tau": [0.1, 0.2]})
    assert set(weights.factors) <= set(MODES)
    with pytest.raises(AdmissionCubeError):
        AdmissionWeights(factors={"unnamed": [1, 2, 3]})
    with pytest.raises(AdmissionCubeError):
        AdmissionWeights(factors={"probe": [1]})
