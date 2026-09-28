# === CHECKS ===
# id: check_respond_v0_uses_infer
#   proves: respond_v0_uses_infer
#   call: self::test_uses_infer
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_respond_v0_one_motion_card_no_winner
#   proves: respond_v0_one_motion_card_no_winner
#   call: self::test_one_motion_card_no_winner
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_respond_v0_empty_is_not_an_answer
#   proves: respond_v0_empty_is_not_an_answer
#   call: self::test_empty_is_not_an_answer
#   requires: python3
#   timeout: 30
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_respond_v0_named_refusals
#   proves: respond_v0_named_refusals
#   call: self::test_named_refusals
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# === END CHECKS ===
from hashlib import sha256
import os
from pathlib import Path

import pytest

import english_gonol.respond_v0 as respond_module
from english_gonol.full_construct_run import build_construct
from english_gonol.inference_input import EnglishConstruct
from english_gonol.inference_v0 import Bundle, Refusal
from english_gonol.language.source import LexemeRecord, SenseRecord, SynsetRecord, WordnetSnapshot
from english_gonol.respond_v0 import respond

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


def test_uses_infer(artifact, monkeypatch):
    with _open(artifact) as corpus:
        captured = {}

        def fake_infer(frame, corpus_arg, ucns_root):
            captured["frame"] = frame
            return []

        monkeypatch.setattr(respond_module, "infer", fake_infer)
        response = respond("alpha letter alpha.", corpus, UCNS_SOURCE_ROOT)
        assert captured["frame"].text == "alpha letter alpha."
        assert response["bundle_count_hidden"] == 0


def test_one_motion_card_no_winner(artifact):
    with _open(artifact) as corpus:
        response = respond("alpha letter alpha.", corpus, UCNS_SOURCE_ROOT)
        assert response["words"] == ["alpha", "letter", "alpha."]
        assert response["def_ids"] == [1, 2]
        assert len(response["def_ids"]) <= 8
        card = response["motion_card"]
        assert card is not None
        assert card["sample_not_selected"] is True
        assert set(card) >= {"map_id", "definition_id", "channels", "lifted", "placement"}
        assert card["lifted"]["phase_turns"]
        assert card["placement"]["angle_turn"]
        assert response["bundle_count_hidden"] > 1
        assert response["hmmm"] == "no winner"


def test_empty_is_not_an_answer(artifact):
    with _open(artifact) as corpus:
        response = respond("", corpus, UCNS_SOURCE_ROOT)
        assert response["words"] == []
        assert response["def_ids"] == []
        assert response["motion_card"] is None
        assert response["bundle_count_hidden"] == 0
        assert response["empty_is_not_an_answer"] is True


def test_named_refusals(artifact):
    with _open(artifact) as corpus:
        response = respond("alpha letter alpha.", corpus, UCNS_SOURCE_ROOT, K="other")
        assert response["motion_card"] is None
        assert response["refuse"] == [
            {"map_id": "K", "clause": "not determined: only K='one-def' is implemented"}
        ]
        with pytest.raises(TypeError):
            respond(None, corpus, UCNS_SOURCE_ROOT)
