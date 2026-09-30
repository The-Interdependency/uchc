# === CHECKS ===
# id: check_epicyclic_consumer_edges_are_bundles
#   proves: epicyclic_consumer_edges_are_bundles
#   call: self::test_edges_are_bundles
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_epicyclic_consumer_refusals_are_named
#   proves: epicyclic_consumer_refusals_are_named
#   call: self::test_refusals_are_named
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_epicyclic_consumer_full_record_replays
#   proves: epicyclic_consumer_full_record_replays
#   call: self::test_full_record_replays
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# === END CHECKS ===
import json
import os
from hashlib import sha256
from pathlib import Path

import pytest

from english_gonol.epicyclic_consumer import (
    EpicyclicConsumerError,
    build_sentence_epicyclic_graph,
    read_full_graph_record,
    write_full_graph_record,
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


def test_edges_are_bundles(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:epicyclic").require_complete()
        record = build_sentence_epicyclic_graph(frame, corpus, UCNS_SOURCE_ROOT)
        assert record["edge_count"] == len(record["edges"])
        assert record["graph"]["edge_count"] == record["edge_count"]
        for entry in record["edges"]:
            assert "map_id" in entry and "definition_id" in entry
            edge = entry["edge"]
            assert len(edge["connection"]) == 3
            assert len(edge["expansion"]["circle_cover"]) == 3


def test_refusals_are_named(artifact):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:refused").require_complete()
        record = build_sentence_epicyclic_graph(frame, corpus, UCNS_SOURCE_ROOT)
        for refusal in record["refused_connections"]:
            assert set(refusal) >= {"map_id", "definition_id", "clause"}


def test_full_record_replays(artifact, tmp_path):
    with _open(artifact) as corpus:
        frame = corpus.resolve_text("alpha letter alpha.", source_id="fixture:replay").require_complete()
        record = build_sentence_epicyclic_graph(frame, corpus, UCNS_SOURCE_ROOT)
        path = write_full_graph_record(record, tmp_path / "graph.json")
        replayed = read_full_graph_record(path.read_bytes(), UCNS_SOURCE_ROOT)
        assert replayed["receipt_sha256"] == record["receipt_sha256"]

        tampered = bytearray(path.read_bytes())
        tampered[40] ^= 0x01
        with pytest.raises((EpicyclicConsumerError, json.JSONDecodeError)):
            read_full_graph_record(bytes(tampered), UCNS_SOURCE_ROOT)
