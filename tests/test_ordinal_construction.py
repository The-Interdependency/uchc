# ratios: loc_comments=155:63 imports_exports=8:10 calls_definitions=76:10
# SPDX-License-Identifier: FSL-1.1-ALv2
# Copyright 2026 Erin Spencer
# === CHECKS ===
# id: check_ordinal_ucns_exact_prefixes
#   proves: uchc_ordinal_ucns_is_the_sole_geometry_authority, uchc_ordinal_glyph_occurrences_preserve_geometry
#   call: self::test_word_prefixes_and_exact_positions
#   requires: python3, pytest
#   timeout: 30
#   mutates: none
#   cleanup: none
# id: check_ordinal_repeated_glyphs
#   proves: uchc_ordinal_glyph_occurrences_preserve_geometry
#   call: self::test_repeated_glyphs_keep_angle_and_distinct_radii
#   requires: python3, pytest
#   timeout: 30
#   mutates: none
#   cleanup: none
# id: check_ordinal_missing_public_angles
#   proves: uchc_ordinal_no_fabricated_angles
#   call: self::test_missing_public_gonol_angles_fail_closed
#   requires: python3, pytest
#   timeout: 30
#   mutates: none
#   cleanup: none
# id: check_ordinal_space_is_reference
#   proves: uchc_ordinal_no_fabricated_angles
#   call: self::test_space_is_origin_not_radial_glyph
#   requires: python3, pytest
#   timeout: 30
#   mutates: none
#   cleanup: none
# id: check_ordinal_source_drift
#   proves: uchc_ordinal_no_fabricated_angles
#   call: self::test_source_drift_refuses
#   requires: python3, pytest
#   timeout: 30
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_ordinal_rejects_unrelated_ucns_frames
#   proves: uchc_ordinal_ucns_is_the_sole_geometry_authority, uchc_ordinal_no_fabricated_angles
#   call: self::test_geometry_record_never_mislabels_non_glyph_frames
#   requires: python3, pytest
#   timeout: 30
#   mutates: none
#   cleanup: none
# id: check_ordinal_partial_corpus
#   proves: uchc_ordinal_no_fabricated_angles, uchc_ordinal_query_consumes_verified_word_interiors
#   call: self::test_partial_corpus_refuses_public_binding
#   requires: python3, pytest
#   timeout: 60
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_ordinal_reconstruction
#   proves: uchc_ordinal_glyph_occurrences_preserve_geometry
#   call: self::test_all_short_sequences_match_independent_append_oracle
#   requires: python3, pytest
#   timeout: 30
#   mutates: none
#   cleanup: none
# === END CHECKS ===

"""UCHC consumer contract: run with pinned UCNS installed (no UCNS stubs)."""
from fractions import Fraction
from itertools import product
import importlib
from pathlib import Path

import pytest

from english_gonol.ordinal_construction import (
    OrdinalGeometryError,
    OrdinalStructuralField,
    _ucns,
    construct_glyph_gonol,
    geometry_record,
    PUBLIC_GONOL_SHA256,
    UCNS_COMMIT,
)
from english_gonol.language.source import LexemeRecord, SenseRecord, SynsetRecord, WordnetSnapshot
from english_gonol.structural_construct import build

ordinal = importlib.import_module("ucns.ordinal_affixiation")
public = importlib.import_module("ucns.public_gonol")


def test_word_prefixes_and_exact_positions():
    assert public.public_gonol_position(" ") == 0
    cases = ("w", "wo", "wor", "word")
    for source in cases:
        result = construct_glyph_gonol(source)
        assert isinstance(result, ordinal.Construction)
        assert result.origin == "SPACE"
        assert result.recover() == tuple(source)
        assert [result.placement(i).radius() for i in range(len(source))] == [
            Fraction(1, 2 ** (len(source) - i)) for i in range(len(source))
        ]
        assert [result.placement(i).turn for i in range(len(source))] == [
            Fraction(public.public_gonol_position(glyph), 157) for glyph in source
        ]

    word = construct_glyph_gonol("word")
    assert [word.placement(i).radius() for i in range(4)] == [
        Fraction(1, 16), Fraction(1, 8), Fraction(1, 4), Fraction(1, 2)
    ]
    record = geometry_record(word)
    assert record["geometry_authority"]["commit"] == UCNS_COMMIT
    assert record["geometry_authority"]["public_gonol_sha256"] == PUBLIC_GONOL_SHA256
    assert record["recovered_glyphs"] == list("word")
    assert [p["radius"]["power_of_two_denominator"] for p in record["construction"]["placements"]] == [4, 3, 2, 1]
    assert record["receipt"] == word.receipt


def test_repeated_glyphs_keep_angle_and_distinct_radii():
    obj = construct_glyph_gonol("wow")
    assert obj.participants[0].identity == obj.participants[2].identity == "w"
    assert obj.placement(0).turn == obj.placement(2).turn
    assert obj.placement(0).radius() == Fraction(1, 8)
    assert obj.placement(2).radius() == Fraction(1, 2)
    assert obj.recover() == ("w", "o", "w")
    assert construct_glyph_gonol("wow", source="v1").receipt != construct_glyph_gonol("wow", source="v2").receipt


def test_all_short_sequences_match_independent_append_oracle():
    for n in range(1, 6):
        for chars in product("wo", repeat=n):
            obj = construct_glyph_gonol("".join(chars))
            radii = []
            for _ in chars:
                radii = [old / 2 for old in radii] + [Fraction(1, 2)]
            assert [obj.placement(i).radius() for i in range(n)] == radii
            assert obj.recover() == chars


def test_missing_public_gonol_angles_fail_closed():
    for invalid, code in (
        ("", "NONEMPTY_GLYPH_SEQUENCE_REQUIRED"),
        (None, "NONEMPTY_GLYPH_SEQUENCE_REQUIRED"),
        ("\ud800", "UNICODE_SCALAR_REQUIRED"),
        ("w🦄", "PUBLIC_GONOL_ANGLE_UNAVAILABLE"),
        ("é", "PUBLIC_GONOL_ANGLE_UNAVAILABLE"),
    ):
        with pytest.raises(OrdinalGeometryError) as exc:
            construct_glyph_gonol(invalid)
        assert exc.value.code == code
    with pytest.raises(OrdinalGeometryError) as exc:
        construct_glyph_gonol("word", source="")
    assert exc.value.code == "SOURCE_IDENTITY_REQUIRED"
    assert public.public_gonol_sha256() == PUBLIC_GONOL_SHA256


def test_space_is_origin_not_radial_glyph():
    assert public.public_gonol_position(" ") == 0
    for text in (" ", "w o", "word "):
        with pytest.raises(OrdinalGeometryError) as exc:
            construct_glyph_gonol(text)
        assert exc.value.code == "SPACE_SEAM_REQUIRES_FRAME_ATTACHMENT"


def test_source_drift_refuses(tmp_path, monkeypatch):
    fixture = tmp_path / "forged.py"
    fixture.write_text("def affine_radius(i): return 17\n", encoding="utf-8")
    with monkeypatch.context() as patch:
        patch.setattr(ordinal, "__file__", str(fixture))
        _ucns.cache_clear()
        with pytest.raises(OrdinalGeometryError) as exc:
            construct_glyph_gonol("word")
        assert exc.value.code == "UCNS_PRODUCER_DRIFT"
    _ucns.cache_clear()
    assert construct_glyph_gonol("word").recover() == tuple("word")

    with monkeypatch.context() as patch:
        patch.setattr(public, "PUBLIC_GONOL_SHA256", "0" * 64)
        _ucns.cache_clear()
        with pytest.raises(OrdinalGeometryError) as exc:
            construct_glyph_gonol("word")
        assert exc.value.code == "PUBLIC_GONOL_CARRIER_DRIFT"
    _ucns.cache_clear()


def test_partial_corpus_refuses_public_binding(tmp_path):
    source = WordnetSnapshot(
        lexemes=(LexemeRecord("word", "n", (), (SenseRecord("s1", "n1", ()),)),),
        synsets=(SynsetRecord("n1", "n", ("word",), ("word",), ()),),
        source_tree_sha256="0" * 64,
        source_file_count=1,
    )
    state = tmp_path / "partial"
    build(source, out_dir=state, public_position=lambda _c: None,
          producer={"standing": "fixture-only"})
    with OrdinalStructuralField(state) as field:
        graph = field.construct("word")
        assert graph["logical_state"] == "closed"
        result = field.geometry(graph, operation="ordinal-affixiation")
        assert result["standing"] == "refused"
        assert result["code"] == "COMPLETE_CORPUS_REQUIRED_FOR_PUBLIC_GONOL"
        logical = field.compose(graph, relation="ordered-text")
        assert logical["standing"] == "logically-closed"
        assert logical["geometry_state"] == "hmmm:COMPLETE_CORPUS_REQUIRED_FOR_PUBLIC_GONOL"
        with pytest.raises(OrdinalGeometryError) as exc:
            field.word("word")
        assert exc.value.code == "COMPLETE_CORPUS_REQUIRED_FOR_PUBLIC_GONOL"
        assert field.geometry(graph, operation="displacement")["code"] == "UCNS_OPERATION_REQUIRED"


def test_ucns_nested_construction_retains_word_interior():
    first = construct_glyph_gonol("word")
    # No higher-order English angle is asserted: the word carrier is an
    # explicitly supplied test relation, and UCNS owns its geometry.
    carrier = ordinal.Carrier(("word", "other"), "test:explicit-word-carrier")
    sentence = ordinal.affixiate(
        "test:word-twice",
        (ordinal.Participant.closed(carrier, first),
         ordinal.Participant.closed(carrier, first)),
        origin="SPACE", relation="test:declared", source="test:nesting",
    )
    assert sentence.recover() == tuple("wordword")
    assert sentence.participants[0].interior is first
    assert sentence.participants[1].interior is first



def test_geometry_record_never_mislabels_non_glyph_frames():
    public_word = construct_glyph_gonol("word")
    other = ordinal.Carrier(("word", "other"), "fixture:word-carrier")
    unrelated = ordinal.affixiate(
        "test:word", (ordinal.Participant.closed(other, public_word),),
        origin="SPACE", relation="test:word-promotion", source="fixture",
    )
    for obj in (unrelated, ordinal.affixiate(
        "word", public_word.participants,
        origin="OTHER", relation=public_word.relation, source="fixture",
    ), ordinal.affixiate(
        "word", public_word.participants,
        origin="SPACE", relation="unrelated-relation", source="fixture",
    )):
        with pytest.raises(OrdinalGeometryError) as exc:
            geometry_record(obj)
        assert exc.value.code == "UCNS_PUBLIC_GLYPH_CONSTRUCTION_REQUIRED"
    assert geometry_record(public_word)["receipt"] == public_word.receipt


def test_geometry_record_refuses_fake_construction():
    with pytest.raises(OrdinalGeometryError) as exc:
        geometry_record({"receipt": "made-up"})
    assert exc.value.code == "UCNS_CONSTRUCTION_REQUIRED"
# ratios: loc_comments=155:63 imports_exports=8:10 calls_definitions=76:10
