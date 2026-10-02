# === CHECKS ===
# id: check_hilbert_basis_is_uchc_axes_not_cartesian
#   proves: hilbert_basis_is_uchc_axes_not_cartesian
#   call: self::test_origin_local_basis_and_inner_product
#   requires: python3
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_hilbert_inner_product_is_origin_local
#   proves: hilbert_inner_product_is_origin_local
#   call: self::test_cross_origin_inner_product_fails_closed
#   requires: python3
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_hilbert_word_promotion_preserves_order_and_multiplicity
#   proves: hilbert_word_promotion_preserves_order_and_multiplicity
#   call: self::test_word_promotion_preserves_glyph_order_and_multiplicity
#   requires: python3
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_hilbert_frame_state_preserves_occurrence_order
#   proves: hilbert_frame_state_preserves_occurrence_order
#   call: self::test_frame_basis_state_preserves_word_and_whitespace_axes
#   requires: python3
#   timeout: 30
#   mutates: none
#   cleanup: none
#
# id: check_hilbert_finite_origin_spaces_are_complete
#   proves: hilbert_finite_origin_spaces_are_complete
#   call: self::test_finite_origin_spaces_report_complete
#   requires: python3
#   timeout: 30
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

from dataclasses import dataclass

import pytest

from english_gonol.hilbert_inference import (
    HilbertInferenceError,
    basis_vector,
    frame_basis_state,
    glyph_axis,
    glyph_space,
    word_axis,
    word_promotion,
    word_space,
)
from english_gonol.hyperspace_construct import GlyphGonol, WordGonol
from english_gonol.inference_input import (
    ConstructIdentity,
    GlyphOccurrence,
    InferenceFrame,
    TextOccurrence,
    WordRecord,
)


@dataclass
class _Corpus:
    inventory: dict[str, GlyphGonol]
    words: dict[int, WordRecord]

    def word_by_id(self, word_id: int) -> WordRecord:
        return self.words[word_id]

    def iter_words(self):
        yield from self.words.values()


def _corpus() -> _Corpus:
    inventory = {
        "a": GlyphGonol("a", 0, "carrier", ("a",), 0),
        "b": GlyphGonol("b", 1, "carrier", ("b",), 1),
        " ": GlyphGonol(" ", 2, "carrier", (" ",), 2),
    }
    words = {
        1: WordRecord("receipt", WordGonol(1, "ab", (1, 2), 1), ()),
        2: WordRecord("receipt", WordGonol(2, "a", (1,), 2), ()),
        3: WordRecord("receipt", WordGonol(3, "aa", (1, 1), 3), ()),
    }
    return _Corpus(inventory, words)


def _frame(corpus: _Corpus, text: str = "ab a") -> InferenceFrame:
    identity = ConstructIdentity("0" * 64, "1" * 64, (), "test")
    glyphs = tuple(
        GlyphOccurrence(index, scalar, index, index + 1, index + 1, corpus.inventory[scalar])
        for index, scalar in enumerate(text)
    )
    occurrences = (
        TextOccurrence(0, "word", "ab", 0, 2, 0, 2, 1),
        TextOccurrence(1, "character", " ", 2, 3, 2, 3, 3),
        TextOccurrence(2, "word", "a", 3, 4, 3, 4, 2),
    )
    return InferenceFrame(
        identity,
        "test:hilbert",
        text,
        glyphs,
        occurrences,
        (corpus.words[1], corpus.words[2]),
    )


def test_origin_local_basis_and_inner_product() -> None:
    corpus = _corpus()
    a = basis_vector(glyph_axis(corpus.inventory["a"]), scalar_field="R")
    b = basis_vector(glyph_axis(corpus.inventory["b"]), scalar_field="R")

    assert a.inner_product(a) == 1.0
    assert a.inner_product(b) == 0.0
    vector = a.scale(2).add(b.scale(3))
    assert vector.norm_squared() == 13.0

    complex_a = basis_vector(glyph_axis(corpus.inventory["a"]), scalar_field="C")
    rotated = complex_a.scale(1j)
    assert rotated.norm_squared() == 1.0


def test_cross_origin_inner_product_fails_closed() -> None:
    corpus = _corpus()
    glyph = basis_vector(glyph_axis(corpus.inventory["a"]), scalar_field="R")
    word = basis_vector(word_axis(corpus.words[2].gonol), scalar_field="R")

    with pytest.raises(HilbertInferenceError, match="cross-origin"):
        glyph.inner_product(word)


def test_word_promotion_preserves_glyph_order_and_multiplicity() -> None:
    corpus = _corpus()

    ab = word_promotion(corpus, 1)
    assert [axis.identity for axis in ab.source.factors] == ["a", "b"]
    assert ab.target == word_axis(corpus.words[1].gonol)

    aa = word_promotion(corpus, 3)
    assert [axis.identity for axis in aa.source.factors] == ["a", "a"]
    assert len(aa.source.factors) == 2
    assert aa.target == word_axis(corpus.words[3].gonol)


def test_frame_basis_state_preserves_word_and_whitespace_axes() -> None:
    corpus = _corpus()
    state = frame_basis_state(_frame(corpus), corpus)

    assert state.space_signature == ("O_W", "O_G", "O_W")
    assert [(axis.identity_kind, axis.identity) for axis in state.factors] == [
        ("word", "1"),
        ("glyph", " "),
        ("word", "2"),
    ]
    assert state.norm() == 1.0


def test_empty_frame_has_no_inference_basis_state() -> None:
    corpus = _corpus()
    identity = ConstructIdentity("0" * 64, "1" * 64, (), "test")
    frame = InferenceFrame(identity, "test:empty", "", (), (), ())

    with pytest.raises(HilbertInferenceError, match="empty input"):
        frame_basis_state(frame, corpus)


def test_finite_origin_spaces_report_complete() -> None:
    corpus = _corpus()
    glyphs = glyph_space(corpus, scalar_field="R")
    words = word_space(corpus, scalar_field="C")

    assert glyphs.dimension == 3
    assert words.dimension == 3
    assert glyphs.scalar_field == "R"
    assert words.scalar_field == "C"
    assert glyphs.complete is True
    assert words.complete is True
