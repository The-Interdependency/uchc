# === CHECKS ===
# id: check_inference_v0_option_preserving
#   proves: inference_v0_option_preserving
#   call: self::test_option_preserving
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_inference_v0_named_refusals
#   proves: inference_v0_named_refusals
#   call: self::test_named_refusals
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_inference_v0_receipts_record_both_angle_stories
#   proves: inference_v0_receipts_record_both_angle_stories
#   call: self::test_receipts_record_both_angle_stories
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_inference_v0_covering_recorded_not_searched
#   proves: inference_v0_covering_recorded_not_searched
#   call: self::test_covering_recorded_not_searched
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_inference_v0_zero_is_identity
#   proves: inference_v0_zero_is_identity
#   call: self::test_zero_is_identity
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# === END CHECKS ===
from hashlib import sha256
import os
from pathlib import Path

import pytest

from english_gonol.full_construct_run import build_construct
from english_gonol.inference_input import EnglishConstruct
from english_gonol.inference_v0 import (
    Refusal,
    bundle_bytes,
    infer,
    infer_definition,
    zero_channel_control,
)
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


def test_option_preserving(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:v0").require_complete()
        bundles = infer(frame, corpus, UCNS_SOURCE_ROOT)
        fired = [bundle for bundle in bundles if bundle.receipts is not None]
        expected = sum(len(word.definition_ids) for word in frame.words) * 4 * 4 * 3
        assert len(bundles) == expected  # defs * O * S * C
        assert fired
        # at least two distinct runnable maps on one real admitted frame
        map_ids = {bundle.map_id for bundle in fired}
        assert len(map_ids) >= 2
        # definition IDs not collapsed
        definition_ids = {bundle.definition_id for bundle in bundles}
        assert len(definition_ids) == 2


def test_named_refusals(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("another word", source_id="fixture:refusal").require_complete()
        alpha = corpus.word("alpha")
        bundles = infer_definition(frame, corpus, alpha.definition_ids[0], UCNS_SOURCE_ROOT)
        refusals = [
            refusal
            for bundle in bundles
            for refusal in bundle.refusals
        ]
        assert refusals
        clauses = {refusal.clause for refusal in refusals}
        assert "identity/occurrence collapse" in clauses
        refused_bundles = [bundle for bundle in bundles if bundle.refusals]
        assert all(bundle.receipts is None for bundle in refused_bundles)
        assert all(type(refusal) is Refusal for refusal in refusals)


def test_receipts_record_both_angle_stories(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:receipts").require_complete()
        fired = [bundle for bundle in infer(frame, corpus, UCNS_SOURCE_ROOT) if bundle.receipts]
        assert fired
        bundle = fired[0]
        assert "composite" in bundle.receipts
        assert "lifted_unset" in bundle.receipts
        assert "placement" in bundle.receipts
        assert "readout" in bundle.receipts
        assert "lifted + placement" in bundle.receipts["readout"]
        # replay byte-stable
        again = infer(frame, corpus, UCNS_SOURCE_ROOT)
        assert bundle_bytes(again[0]) == bundle_bytes(bundle)
        assert bundle_bytes(again[0]) == bundle.bytes()


def test_covering_recorded_not_searched(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:covering").require_complete()
        bundle = infer(frame, corpus, UCNS_SOURCE_ROOT)[0]
        assert bundle.covering == {"unset": True, "bijective_d": 158, "searched": False}


def test_zero_is_identity(artifact):
    report = zero_channel_control(UCNS_SOURCE_ROOT)
    assert report["identity_ok"] is True
