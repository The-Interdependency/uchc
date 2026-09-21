from __future__ import annotations

import json
from pathlib import Path

import pytest

from english_gonol.definition_affixiation_run import (
    GEOMETRY_REASON,
    GEOMETRY_STATE,
    GonolAffixiationRunError,
    run,
    verify_replay,
)
from english_gonol.language.source import (
    LexemeRecord,
    SenseRecord,
    SynsetRecord,
    WordnetSnapshot,
)


def _snapshot() -> WordnetSnapshot:
    return WordnetSnapshot(
        lexemes=(
            LexemeRecord(
                "kind",
                "n",
                ("kinder",),
                (SenseRecord("kind%1", "kind-n", ()),),
            ),
            LexemeRecord(
                "ice cream",
                "n",
                (),
                (SenseRecord("ice_cream%1", "ice-cream-n", ()),),
            ),
            LexemeRecord(
                "trio",
                "n",
                (),
                (
                    SenseRecord("trio%1", "trio-1-n", ()),
                    SenseRecord("trio%2", "trio-2-n", ()),
                    SenseRecord("trio%3", "trio-3-n", ()),
                ),
            ),
        ),
        synsets=(
            SynsetRecord(
                "kind-n",
                "n",
                ("kind",),
                ("having a friendly generous nature",),
                (),
            ),
            SynsetRecord(
                "ice-cream-n",
                "n",
                ("ice cream",),
                ("a frozen dessert made from cream",),
                (),
            ),
            SynsetRecord(
                "trio-1-n",
                "n",
                ("trio",),
                ("first definition",),
                (),
            ),
            SynsetRecord(
                "trio-2-n",
                "n",
                ("trio",),
                ("second definition",),
                (),
            ),
            SynsetRecord(
                "trio-3-n",
                "n",
                ("trio",),
                ("third definition",),
                (),
            ),
        ),
        source_tree_sha256="0" * 64,
        source_file_count=2,
    )


def _read_lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_full_fixture_run_persists_and_replays(tmp_path: Path) -> None:
    manifest = run(_snapshot(), out_dir=tmp_path, workers=1)
    records = _read_lines(tmp_path / "records.jsonl")

    words = [record for record in records if record["type"] == "word"]
    whitespace = [record for record in records if record["type"] == "whitespace"]
    definitions = [record for record in records if record["type"] == "definition"]
    affixiations = [record for record in records if record["type"] == "affixiation"]

    # No sampling: every sense and every definition is processed.
    assert manifest["counts"]["definition_gonols"] == 5
    assert len(definitions) == 5
    assert len(affixiations) == 10
    # Whitespace is construction, not parsing.
    assert manifest["whitespace"]["preserved"] is True
    assert manifest["whitespace"]["whitespace_gonols"] >= 1
    assert any(record["surface"] == " " for record in whitespace)

    # No hash placement: word identity is the exact surface source id,
    # including multiword surfaces with their exact whitespace.
    word_sources = {record["source_id"] for record in words}
    assert "oewn:surface:kind" in word_sources
    assert "oewn:surface:kinder" in word_sources
    assert "oewn:surface:a" in word_sources
    assert "oewn:surface:ice cream" in word_sources
    for record in words:
        assert record["atomic_id"] and len(record["atomic_id"]) == 64

    # Definitions preserve sense identity, order, and constituent identities;
    # whitespace scalars participate between the word gonols.
    by_sense = {record["sense_id"]: record for record in definitions}
    assert by_sense["kind%1"]["constituent_source_ids"][0] == "oewn:surface:having"
    assert by_sense["ice_cream%1"]["word_source_id"] == "oewn:surface:ice cream"
    ice_ids = by_sense["ice_cream%1"]["constituent_source_ids"]
    assert ice_ids == [
        "oewn:surface:a",
        "oewn:whitespace:32",
        "oewn:surface:frozen",
        "oewn:whitespace:32",
        "oewn:surface:dessert",
        "oewn:whitespace:32",
        "oewn:surface:made",
        "oewn:whitespace:32",
        "oewn:surface:from",
        "oewn:whitespace:32",
        "oewn:surface:cream",
    ]
    assert by_sense["ice_cream%1"]["whitespace_preserved"] is True

    # Orthogonal affixiation boundary is exposed with no invented substitute.
    for record in affixiations:
        assert record["geometry_state"] == GEOMETRY_STATE
        assert "UCNS orthogonal-affixiation geometry is unresolved" in record["reason"]
    assert manifest["ucns"]["orthogonal_affixiation_geometry"] == GEOMETRY_STATE
    assert manifest["ucns"]["orthogonal_affixiation_reason"] == GEOMETRY_REASON

    # Definition topology: both the sequential chain and the direct
    # word-to-each-definition structure are recorded for the same word.
    trio_word = "oewn:surface:trio"
    trio_definitions = sorted(
        (record for record in definitions if record["word_source_id"] == trio_word),
        key=lambda record: record["order"],
    )
    assert [record["definition_source_id"] for record in trio_definitions] == [
        "oewn:def:trio%1:0",
        "oewn:def:trio%2:0",
        "oewn:def:trio%3:0",
    ]
    assert [record["order"] for record in trio_definitions] == [1, 2, 3]

    trio_chain = [
        record
        for record in affixiations
        if record["word_source_id"] == trio_word and record["structure"] == "chain"
    ]
    trio_direct = [
        record
        for record in affixiations
        if record["word_source_id"] == trio_word and record["structure"] == "direct"
    ]
    assert [(record["order"], record["orthogonal_to"], record["definition_source_id"]) for record in trio_chain] == [
        (1, trio_word, "oewn:def:trio%1:0"),
        (2, "oewn:def:trio%1:0", "oewn:def:trio%2:0"),
        (3, "oewn:def:trio%2:0", "oewn:def:trio%3:0"),
    ]
    assert [(record["order"], record["orthogonal_to"], record["definition_source_id"]) for record in trio_direct] == [
        (1, trio_word, "oewn:def:trio%1:0"),
        (2, trio_word, "oewn:def:trio%2:0"),
        (3, trio_word, "oewn:def:trio%3:0"),
    ]
    assert manifest["counts"]["chain_affixiations"] == 5
    assert manifest["counts"]["direct_affixiations"] == 5
    assert manifest["counts"]["affixiation_records"] == 10

    # Per-word definition order is sequential and starts at 1.
    assert [record["order"] for record in definitions if record["word_source_id"].endswith("kind")] == [1]

    # Deterministic replay verifies; a tampered records file fails closed.
    assert verify_replay(tmp_path)["schema"] == manifest["schema"]
    (tmp_path / "records.jsonl").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(GonolAffixiationRunError):
        verify_replay(tmp_path)


def test_run_requires_empty_output_directory(tmp_path: Path) -> None:
    (tmp_path / "stale.txt").write_text("x", encoding="utf-8")
    with pytest.raises(GonolAffixiationRunError):
        run(_snapshot(), out_dir=tmp_path, workers=1)


def test_workers_path_is_deterministic(tmp_path: Path) -> None:
    single = tmp_path / "single"
    multi = tmp_path / "multi"
    single_manifest = run(_snapshot(), out_dir=single, workers=1)
    multi_manifest = run(_snapshot(), out_dir=multi, workers=2)
    assert single_manifest["records_sha256"] == multi_manifest["records_sha256"]
    assert verify_replay(multi)["replay_digest"] == multi_manifest["replay_digest"]
