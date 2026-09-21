from __future__ import annotations

import pytest

from english_gonol.gonol import (
    GonolConstructionError,
    construct_gonol,
    replay_gonol,
)
from english_gonol.language.character_definitions import build_character_definition_layer
from english_gonol.language.suffixiation import suffixiate


def test_suffixiation_preserves_y_before_ing_from_y_definition_space() -> None:
    layer = build_character_definition_layer()
    base = construct_gonol(scale="word", source="try", source_id="fixture:try")
    ing = construct_gonol(
        scale="suffix",
        source="ing",
        source_id="fixture:ing",
        carried_options=(("suffix-coupling.vowel-initial", "true"),),
    )
    result = suffixiate(base.gonol, ing.gonol, source_id="fixture:trying", layer=layer)

    assert result.y_realization == "preserve-y"
    assert result.suffix_vowel_initial is True
    assert result.coupling_receipt.gonol.relation == "suffix-coupling"
    assert result.coupling_receipt.gonol.participants == (base.gonol, ing.gonol)
    assert result.coupling_receipt.receipt_digest == replay_gonol(
        receipt=result.coupling_receipt
    ).receipt_digest


def test_suffixiation_resolves_y_to_i_before_vowel_initial_non_ing() -> None:
    layer = build_character_definition_layer()
    base = construct_gonol(scale="word", source="try", source_id="fixture:try")
    ed = construct_gonol(
        scale="suffix",
        source="ed",
        source_id="fixture:ed",
        carried_options=(("suffix-coupling.vowel-initial", "true"),),
    )
    result = suffixiate(base.gonol, ed.gonol, source_id="fixture:tried", layer=layer)
    assert result.y_realization == "y-to-i"


def test_suffixiation_does_not_resolve_y_after_vowel() -> None:
    layer = build_character_definition_layer()
    base = construct_gonol(scale="word", source="play", source_id="fixture:play")
    ing = construct_gonol(
        scale="suffix",
        source="ing",
        source_id="fixture:ing",
        carried_options=(("suffix-coupling.vowel-initial", "true"),),
    )
    result = suffixiate(base.gonol, ing.gonol, source_id="fixture:playing", layer=layer)
    assert result.y_realization is None


def test_suffixiation_does_not_reopen_participants() -> None:
    layer = build_character_definition_layer()
    base = construct_gonol(scale="word", source="try", source_id="fixture:try")
    ing = construct_gonol(
        scale="suffix",
        source="ing",
        source_id="fixture:ing",
        carried_options=(("suffix-coupling.vowel-initial", "true"),),
    )
    base_before = base.gonol.receipt_digest
    ing_before = ing.gonol.receipt_digest
    result = suffixiate(base.gonol, ing.gonol, source_id="fixture:trying", layer=layer)
    assert result.coupling_receipt.gonol.participants[0].receipt_digest == base_before
    assert result.coupling_receipt.gonol.participants[1].receipt_digest == ing_before


def test_suffixiation_requires_closed_suffix_gonol() -> None:
    word = construct_gonol(scale="word", source="ing", source_id="fixture:not-suffix")
    base = construct_gonol(scale="word", source="try", source_id="fixture:try")
    with pytest.raises(GonolConstructionError, match="closed suffix gonol"):
        suffixiate(base.gonol, word.gonol, source_id="fixture:bad")
