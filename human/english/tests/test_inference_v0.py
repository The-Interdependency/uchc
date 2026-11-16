from hashlib import sha256

import pytest

from english_gonol.full_construct_run import build_construct
from english_gonol.inference_input import EnglishConstruct
from english_gonol.inference_v0 import (
    Refusal,
    bundle_bytes,
    infer,
    infer_definition,
)
from english_gonol.language.source import LexemeRecord, SenseRecord, SynsetRecord, WordnetSnapshot


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
        bundles = infer(frame, corpus)
        fired = [bundle for bundle in bundles if bundle.channels is not None]
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
        bundles = infer_definition(frame, corpus, alpha.definition_ids[0])
        refusals = [
            refusal
            for bundle in bundles
            for refusal in bundle.refusals
        ]
        assert refusals
        clauses = {refusal.clause for refusal in refusals}
        assert "identity/occurrence collapse" in clauses
        refused_bundles = [bundle for bundle in bundles if bundle.refusals]
        assert all(bundle.channels is None for bundle in refused_bundles)
        assert all(type(refusal) is Refusal for refusal in refusals)


def test_evidence_replays_in_definition_order(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:receipts").require_complete()
        bundles = infer(frame, corpus)
        expected = [d for word in frame.words for d in word.definition_ids for _ in range(48)]
        assert [bundle.definition_id for bundle in bundles] == expected
        fired = next(bundle for bundle in bundles if bundle.channels is not None)
        assert set(fired.as_dict()) == {"map_id", "definition_id", "channels", "refusals", "schema", "version"}
        assert [bundle_bytes(b) for b in infer(frame, corpus)] == [b.bytes() for b in bundles]


def test_dictionary_inference_runs_with_native_imports_blocked(artifact, monkeypatch):
    import builtins

    original = builtins.__import__

    def dictionary_import(name, *args, **kwargs):
        if name.split(".")[0] == "ucns":
            pytest.fail(f"dictionary inference imported {name}")
        return original(name, *args, **kwargs)

    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:portable")
        monkeypatch.setattr(builtins, "__import__", dictionary_import)
        assert infer(frame, corpus)
