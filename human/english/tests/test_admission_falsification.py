# === CHECKS ===
# id: check_where_stream_is_kept
#   proves: where_stream_is_kept
#   call: self::test_where_stream_is_kept
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_unused_where_has_zero_tau
#   proves: unused_where_has_zero_tau
#   call: self::test_unused_where_has_zero_tau
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_where_falsification_uses_infer_only
#   proves: where_falsification_uses_infer_only
#   call: self::test_uses_infer_only
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_where_falsification_standing
#   proves: where_falsification_standing
#   call: self::test_standing
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# === END CHECKS ===
from hashlib import sha256

import pytest
import os
from pathlib import Path

from english_gonol.admission_falsification import run_where_falsification, where_positions
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


def test_where_stream_is_kept(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:where").require_complete()
        positions = where_positions(frame)
        assert len(positions) == 2
        assert all(p.surface.isspace() for p in positions)
        assert all(p.word_id is None for p in positions)


def test_unused_where_has_zero_tau(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:tau0").require_complete()
        report = run_where_falsification(frame, corpus, UCNS_SOURCE_ROOT)
        assert report["unused_where"] == 2
        assert report["tau_from_infer"] == 0
        assert report["clause"] == "not determined"


def test_uses_infer_only(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:inferonly").require_complete()
        report = run_where_falsification(frame, corpus, UCNS_SOURCE_ROOT)
        assert report["no_invented_map_for_space"] is True
        assert report["no_word_id_for_space"] is True
        assert report["no_qk"] is True
        assert all(entry["word_id"] is None for entry in report["where_positions"])


def test_standing(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:standing").require_complete()
        report = run_where_falsification(frame, corpus, UCNS_SOURCE_ROOT)
        assert report["construct"] == "admission"
        assert report["standing"] == "falsified as harmonic substrate"
        again = run_where_falsification(frame, corpus, UCNS_SOURCE_ROOT)
        assert again["receipt_sha256"] == report["receipt_sha256"]
