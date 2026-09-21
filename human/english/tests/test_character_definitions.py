from __future__ import annotations

from english_gonol.language.character_definitions import (
    build_character_definition_layer,
    character_layer_record,
    load_character_definition_table,
)


def test_table_declares_non_exclusive_character_classes() -> None:
    table = load_character_definition_table()
    assert set(table["y"].classes) == {"consonant", "vowel"}
    assert "final-y-after-consonant" in table["y"].orthographic
    assert table["-"].classes == ("operator", "punctuation")
    assert table["3"].number_name == "three"
    assert table["3"].numerology


def test_layer_closes_character_gonols_and_shared_origin_definitions() -> None:
    layer = build_character_definition_layer()
    assert layer.character_gonols["y"].scale == "character"
    assert layer.character_gonols["-"].scale == "character"

    dash_definitions = [
        receipt
        for receipt in layer.definitions
        if receipt.gonol.source_id.startswith("char-def:-:")
    ]
    relations = {receipt.gonol.relation for receipt in dash_definitions}
    assert "char-class:operator" in relations
    assert "char-class:punctuation" in relations
    for receipt in dash_definitions:
        assert receipt.gonol.participants == (layer.character_gonols["-"],)


def test_digit_definitions_compose_number_name_from_characters() -> None:
    layer = build_character_definition_layer()
    number_name_receipts = [
        receipt
        for receipt in layer.definitions
        if receipt.gonol.relation == "digit-number-name" and receipt.gonol.source_id == "char-def:3:number-name"
    ]
    assert len(number_name_receipts) == 1
    receipt = number_name_receipts[0]
    digit_char, number_name_word = receipt.gonol.participants
    assert digit_char == layer.character_gonols["3"]
    assert number_name_word.source_units == ("t", "h", "r", "e", "e")
    assert number_name_word.scale == "word"


def test_layer_is_deterministic_and_replayable() -> None:
    first = build_character_definition_layer()
    second = build_character_definition_layer()
    assert first.receipt_digest == second.receipt_digest
    record = character_layer_record(first)
    assert record["receipt_digest"] == first.receipt_digest
    assert record["definition_receipt_count"] == len(first.definitions)


def test_final_y_realization_uses_y_definition_space() -> None:
    layer = build_character_definition_layer()
    assert layer.final_y_realization("y", "r", "ing", True) == "preserve-y"
    assert layer.final_y_realization("y", "r", "ed", True) == "y-to-i"
    assert layer.final_y_realization("y", "r", "s", True) == "y-to-i"
    assert layer.final_y_realization("y", "a", "ing", True) is None
    assert layer.final_y_realization("x", "r", "ing", True) is None
    assert layer.final_y_realization("y", None, "ing", True) is None


def test_every_public_gonol_glyph_has_a_definition() -> None:
    from english_gonol.language.character_definitions import (
        PUBLIC_GONOL_157,
        PUBLIC_GONOL_SHA256,
    )

    assert len(PUBLIC_GONOL_157) == 157
    assert len(set(PUBLIC_GONOL_157)) == 157
    layer = build_character_definition_layer()

    # Every one of the 157 Public Gonol glyphs has a closed character gonol.
    for glyph in PUBLIC_GONOL_157:
        assert glyph in layer.character_gonols
        assert glyph in layer.entries

    # Every one of them has at least one definition gonol sharing it as origin.
    definitions_by_origin: dict[str, list] = {}
    for receipt in layer.definitions:
        if receipt.gonol.scale != "definition":
            continue
        origin = receipt.gonol.participants[0]
        definitions_by_origin.setdefault(origin.source_units[0], []).append(receipt)
    for glyph in PUBLIC_GONOL_157:
        assert definitions_by_origin.get(glyph), f"Public Gonol glyph {glyph!r} lacks a definition"

    # Glyphs without curated definitions carry an explicit hmmm definition.
    hmmm_origins = {
        receipt.gonol.participants[0].source_units[0]
        for receipt in layer.definitions
        if receipt.gonol.relation == "definition:hmmm"
    }
    curated = {entry.char for entry in layer.entries.values() if not entry.hmmm}
    for glyph in PUBLIC_GONOL_157:
        if glyph not in curated:
            assert glyph in hmmm_origins, f"Public Gonol glyph {glyph!r} lacks its hmmm definition"

    record = character_layer_record(layer)
    assert record["public_gonol_sha256"] == PUBLIC_GONOL_SHA256
    assert record["public_gonol_glyph_count"] == 157
    assert record["public_gonol_glyph_definition_coverage"] == "complete"
