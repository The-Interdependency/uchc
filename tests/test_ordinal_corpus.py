# ratios: loc_comments=45:17 imports_exports=5:2 calls_definitions=12:2
# SPDX-License-Identifier: FSL-1.1-ALv2
# Copyright 2026 Erin Spencer
"""Real-corpus ordinal acceptance; no replacement corpus or geometry mocks.

Usage: set UCHC_STRUCTURAL_FIELD to a verified complete structural field, then
run pytest on this file with pinned UCNS and the selected English package.
The structural workflow runs these checks against both Stack source and the
clean-installed UCHC wheel. Missing corpus configuration is a failure.
"""
from __future__ import annotations

import json
import os

import pytest

from english_gonol.ordinal_construction import OrdinalStructuralField

# === CHECKS ===
# id: check_detached_ordinal_interiors_keep_authority
#   proves: uchc_ordinal_detached_interiors_keep_authority
#   call: self::test_detached_word_and_query_interiors_keep_authority
#   requires: pytest, pinned_ucns, complete_structural_corpus
#   mutates: none
#   cleanup: context_manager_closes_read_only_field
# === END CHECKS ===

EXPECTED_AUTHORITY = {
    "repository": "The-Interdependency/ucns",
    "commit": "ed0b0760f05cd975a7a811f8abeb70a11d09f00b",
    "ordinal_blob": "9fa84ef20f19fe0c04df680f49b50ea307e6d624",
    "public_gonol_blob": "c1955e46e2dc918fb657cb346e42106d71937e91",
    "public_gonol_sha256": "55d10c84529a4d7bc7714786357e977b68d9df2ac3f73d20e229580b552c2ef5",
}


@pytest.fixture(scope="module")
def field():
    path = os.environ.get("UCHC_STRUCTURAL_FIELD")
    if not path:
        pytest.fail("UCHC_STRUCTURAL_FIELD must name a verified complete corpus")
    with OrdinalStructuralField(path) as opened:
        assert opened.complete_corpus
        yield opened


@pytest.mark.parametrize("text", ["word", "word word", " word  word "])
def test_detached_word_and_query_interiors_keep_authority(field, text):
    word = json.loads(json.dumps(field.word("word")))
    assert word["geometry_authority"] == EXPECTED_AUTHORITY
    assert word["gonal_order"]["identity"] == "word"
    assert [p["radius"]["power_of_two_denominator"]
            for p in word["gonal_order"]["placements"]] == [4, 3, 2, 1]

    query = field.construct(text)
    geometry = field.geometry(query, operation="ordinal-affixiation")
    expected_standing = "partial" if " " in text else "constructed"
    assert geometry["standing"] == expected_standing
    if expected_standing == "partial":
        assert geometry["code"] == "SPACE_SEAM_FRAME_NOT_SELECTED"
        assert "glyph_frame" not in geometry
    else:
        assert geometry["glyph_frame"]["geometry_authority"] == EXPECTED_AUTHORITY
    assert len(geometry["word_interiors"]) == 1
    assert len(geometry["ordered_word_references"]) == len(text.split())
    # Serialized alone, the interior must still name its verified producer.
    interior = json.loads(json.dumps(geometry["word_interiors"][0]))
    assert interior["geometry_authority"] == EXPECTED_AUTHORITY
    assert interior["construction"] == word["gonal_order"]
    assert interior["receipt"] == word["geometry_receipt"]
    composed = field.compose(query, relation="ordered-text")
    assert composed["word_interiors"] == geometry["word_interiors"]
    assert composed["word_interiors"][0]["geometry_authority"] == EXPECTED_AUTHORITY
# ratios: loc_comments=45:17 imports_exports=5:2 calls_definitions=12:2
