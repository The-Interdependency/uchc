from hashlib import sha256
from pathlib import Path

import pytest

import english_gonol.respond_v0 as respond_module
from english_gonol.full_construct_run import build_construct
from english_gonol.inference_input import EnglishConstruct
from english_gonol.language.source import LexemeRecord, SenseRecord, SynsetRecord, WordnetSnapshot
from english_gonol.respond_v0 import respond


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
        response = respond("alpha letter alpha.", corpus)
        assert captured["frame"].text == "alpha letter alpha."
        assert response["bundle_count_hidden"] == 0


def test_one_evidence_card_no_winner(artifact):
    with _open(artifact) as corpus:
        response = respond("alpha letter alpha.", corpus)
        assert response["words"] == ["alpha", "letter", "alpha."]
        assert response["construct"]["database_sha256"] == corpus.identity.database_sha256
        assert response["construct"]["logical_receipt"] == corpus.identity.logical_receipt
        assert response["def_ids"] == [1, 2]
        assert len(response["def_ids"]) <= 8
        card = response["evidence_card"]
        assert card is not None
        assert card["sample_not_selected"] is True
        assert set(card) == {"map_id", "definition_id", "channels", "refusals", "sample_not_selected", "schema", "version"}
        assert len(card["channels"]) == 3 and card["definition_id"] == 1
        assert response["bundle_count_hidden"] > 1
        assert response["hmmm"] == "no winner"


def test_empty_is_not_an_answer(artifact):
    with _open(artifact) as corpus:
        response = respond("", corpus)
        assert response["words"] == []
        assert response["def_ids"] == []
        assert response["evidence_card"] is None
        assert response["bundle_count_hidden"] == 0
        assert response["empty_is_not_an_answer"] is True


def test_named_refusals(artifact):
    with _open(artifact) as corpus:
        response = respond("alpha letter alpha.", corpus, K="other")
        assert response["evidence_card"] is None
        assert response["refuse"] == [
            {"map_id": "K", "clause": "not determined: only K='one-def' is implemented"}
        ]
        with pytest.raises(TypeError):
            respond(None, corpus)
