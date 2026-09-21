"""Primitive character-definition layer for English Gonol Construction.

Characters are the most primitive admitted gonols. This module closes each
admissible character gonol and attaches its definition gonols, which share
that character gonol as origin. Character definitions are not mutually
exclusive: ``-`` carries both operator and punctuation definitions, and ``y``
carries both vowel and consonant class definitions plus its own orthographic
behavior.

Digit characters close normally as character gonols, then receive a
number-name definition composed from the number name's own word gonol
(``3 -> three -> (t,h,r,e,e)``) plus additional numerology definition gonols.

Nothing in this module is a global morphology law. It is a deterministic,
replayable construction layer over the existing constructor.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from ..gonol import (
    ClosedGonol,
    GonolReceipt,
    construct_gonol,
)

SCHEMA = "english-gonol.character-definitions"
VERSION = "v1"

PUBLIC_GONOL_SHA256 = "55d10c84529a4d7bc7714786357e977b68d9df2ac3f73d20e229580b552c2ef5"

# Frozen copy of the exact 157-position Public Gonol carrier geometry. English
# Gonol Construction holds this only as an immutable identity reference and
# verifies its digest against the pinned constructor authority; it does not
# import or mutate libs/ucns and does not invent UCNS geometry.
PUBLIC_GONOL_157: tuple[str, ...] = (
    " ", "A", "!", '"', "B", "#", "$", "C", "%", "(", "D", "&", "'", "E", "1", "*",
    "F", "+", "[", "G", ",", "-", "H", ".", "/", "I", "3", "{", "J", ":", ";", "K",
    "=", "?", "L", "<", "@", "M", "5", "\\", "N", "^", "_", "O", "\u2018", "`", "P", "|",
    "~", "Q", "7", "\u2026", "R", "\u201c", "\u2014", "S", "\u2013", "\u00b7", "T", "\u00b0", "\u00ab", "U", "9", "\u00b1",
    "V", "\u00d7", "\u00f7", "W", "\u221a", "\u2202", "X", "\u222b", "\u2211", "Y", "\u220f", "\u2207", "Z", "\u221e", "\u2248", "\u2260",
    "a", "\u2264", "\u2265", "b", "\u2192", "\u2190", "c", ")", "\u2191", "d", "\u2193", "2", "e", "\u2194", "\u2295", "f",
    "]", "\u2297", "g", "\u2299", "\u2298", "h", "\u2208", "4", "i", "}", "\u2209", "j", "\u2282", "\u2283", "k", "\u2286",
    ">", "l", "\u2287", "6", "m", "\u2229", "\u222a", "n", "\u2227", "\u2019", "o", "\u2228", "\u00ac", "p", "\u2200", "8",
    "q", "\u2203", "\u201d", "r", "\u22a2", "\u22a8", "s", "\u2234", "\u2235", "t", "\u00bb", "0", "u", "\u2261", "\u03c8", "v",
    "\u03c6", "\u03c9", "w", "\u03b1", "\u03b2", "x", "\u03b3", "\u03b4", "y", "\u03bb", "\u03c0", "z", "\u03c3",
)


def _public_gonol_sha256(arrangement: tuple[str, ...] = PUBLIC_GONOL_157) -> str:
    payload = json.dumps(tuple(arrangement), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


if len(PUBLIC_GONOL_157) != 157 or len(set(PUBLIC_GONOL_157)) != 157:
    raise RuntimeError("frozen Public Gonol copy must have exactly 157 unique glyphs")
if _public_gonol_sha256() != PUBLIC_GONOL_SHA256:
    raise RuntimeError("frozen Public Gonol copy digest does not match the pinned authority")


def _data_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "character_definitions_v1.json"


def _digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class CharacterDefinitionEntry:
    """One character's definition-space summary, recovered from the table."""

    char: str
    classes: tuple[str, ...]
    pronunciation: str | None
    orthographic: tuple[str, ...]
    number_name: str | None
    numerology: tuple[str, ...]
    hmmm: bool = False

    def has_class(self, name: str) -> bool:
        return name in self.classes


@dataclass(frozen=True, slots=True)
class CharacterDefinitionLayer:
    """Closed character gonols and their shared-origin definition gonols."""

    entries: Mapping[str, CharacterDefinitionEntry]
    character_gonols: Mapping[str, ClosedGonol]
    definitions: tuple[GonolReceipt, ...]
    receipt_digest: str

    def final_y_realization(
        self,
        final_character_surface: str,
        preceding_character_surface: str | None,
        suffix_bare: str,
        suffix_vowel_initial: bool,
    ) -> str | None:
        """Resolve final-y rendering from the ``y`` character's own definition-space.

        Returns ``"preserve-y"`` or ``"y-to-i"`` when the final character is a
        ``y`` with the ``final-y-after-consonant`` behavior and the preceding
        character is a consonant, otherwise ``None``.
        """

        entry = self.entries.get(final_character_surface)
        if entry is None or "final-y-after-consonant" not in entry.orthographic:
            return None
        if preceding_character_surface is None:
            return None
        preceding = self.entries.get(preceding_character_surface)
        if preceding is None or not preceding.has_class("consonant"):
            return None
        if suffix_bare == "ing" or not suffix_vowel_initial:
            return "preserve-y"
        return "y-to-i"


def load_character_definition_table(
    path: str | Path | None = None,
) -> dict[str, CharacterDefinitionEntry]:
    source = Path(path) if path is not None else _data_path()
    document = json.loads(source.read_text(encoding="utf-8"))
    if document.get("schema") != SCHEMA or document.get("version") != VERSION:
        raise ValueError("character definition table identity mismatch")

    entries: dict[str, CharacterDefinitionEntry] = {}
    for char, body in document["letters"].items():
        entries[char] = CharacterDefinitionEntry(
            char=char,
            classes=tuple(body["classes"]),
            pronunciation=str(body["pronunciation"]),
            orthographic=tuple(item["behavior"] for item in body.get("orthographic", ())),
            number_name=None,
            numerology=(),
        )
    for char, body in document["digits"].items():
        entries[char] = CharacterDefinitionEntry(
            char=char,
            classes=("digit",),
            pronunciation=None,
            orthographic=(),
            number_name=str(body["number_name"]),
            numerology=tuple(str(item) for item in body["numerology"]),
        )
    for char in document["operators"]:
        existing = entries.get(char)
        entries[char] = CharacterDefinitionEntry(
            char=char,
            classes=tuple(sorted(set((existing.classes if existing else ()) + ("operator",)))),
            pronunciation=existing.pronunciation if existing else None,
            orthographic=existing.orthographic if existing else (),
            number_name=existing.number_name if existing else None,
            numerology=existing.numerology if existing else (),
        )
    for char in document["punctuation"]:
        existing = entries.get(char)
        entries[char] = CharacterDefinitionEntry(
            char=char,
            classes=tuple(sorted(set((existing.classes if existing else ()) + ("punctuation",)))),
            pronunciation=existing.pronunciation if existing else None,
            orthographic=existing.orthographic if existing else (),
            number_name=existing.number_name if existing else None,
            numerology=existing.numerology if existing else (),
        )
    # Every glyph on the Public Gonol carrier must have a definition, even if
    # only hmmm. Glyphs already curated above keep their curated definitions;
    # every remaining Public Gonol glyph receives an explicit hmmm definition.
    for glyph in PUBLIC_GONOL_157:
        if glyph not in entries:
            entries[glyph] = CharacterDefinitionEntry(
                char=glyph,
                classes=(),
                pronunciation=None,
                orthographic=(),
                number_name=None,
                numerology=(),
                hmmm=True,
            )
    return entries


def build_character_definition_layer(
    table: Mapping[str, CharacterDefinitionEntry] | None = None,
) -> CharacterDefinitionLayer:
    """Close every character gonol and attach its definition gonols.

    The returned layer is deterministic and replayable: every definition gonol
    is a normal ``scale="definition"`` closure whose first participant is the
    character gonol that serves as its origin.
    """

    entries = dict(table) if table is not None else load_character_definition_table()
    characters: dict[str, ClosedGonol] = {}
    receipts: list[GonolReceipt] = []

    for char in sorted(entries):
        entry = entries[char]
        character_receipt = construct_gonol(
            scale="character",
            source=char,
            source_id=f"char:{char}",
        )
        characters[char] = character_receipt.gonol
        receipts.append(character_receipt)

        for class_name in entry.classes:
            receipts.append(
                construct_gonol(
                    scale="definition",
                    participants=(character_receipt.gonol,),
                    relation=f"char-class:{class_name}",
                    source_id=f"char-def:{char}:{class_name}",
                )
            )

        if entry.pronunciation:
            receipts.append(
                construct_gonol(
                    scale="definition",
                    participants=(character_receipt.gonol,),
                    relation=f"letter-pronunciation:{entry.pronunciation}",
                    source_id=f"char-def:{char}:letter-pronunciation",
                )
            )

        for behavior in entry.orthographic:
            receipts.append(
                construct_gonol(
                    scale="definition",
                    participants=(character_receipt.gonol,),
                    relation=f"orthographic-behavior:{behavior}",
                    source_id=f"char-def:{char}:orthographic:{behavior}",
                )
            )

        if entry.number_name:
            number_name_receipt = construct_gonol(
                scale="word",
                source=entry.number_name,
                source_id=f"digit-number-name:{entry.number_name}",
            )
            receipts.append(number_name_receipt)
            receipts.append(
                construct_gonol(
                    scale="definition",
                    participants=(character_receipt.gonol, number_name_receipt.gonol),
                    relation="digit-number-name",
                    source_id=f"char-def:{char}:number-name",
                )
            )

        for index, meaning in enumerate(entry.numerology):
            receipts.append(
                construct_gonol(
                    scale="definition",
                    participants=(character_receipt.gonol,),
                    relation=f"numerology:{meaning}",
                    source_id=f"char-def:{char}:numerology:{index}",
                )
            )

        if entry.hmmm:
            receipts.append(
                construct_gonol(
                    scale="definition",
                    participants=(character_receipt.gonol,),
                    relation="definition:hmmm",
                    source_id=f"char-def:{char}:hmmm",
                )
            )

    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "entry_count": len(entries),
        "entries": {
            char: asdict(entry)
            for char, entry in sorted(entries.items())
        },
        "character_receipts": [
            characters[char].receipt_digest for char in sorted(characters)
        ],
        "definition_receipts": [receipt.receipt_digest for receipt in receipts],
    }
    receipt_digest = _digest_bytes(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return CharacterDefinitionLayer(
        entries=entries,
        character_gonols=characters,
        definitions=tuple(receipts),
        receipt_digest=receipt_digest,
    )


def character_layer_record(layer: CharacterDefinitionLayer | None = None) -> dict[str, Any]:
    """Return the deterministic layer artifact payload."""

    value = layer if layer is not None else build_character_definition_layer()
    public_gonol_hmmm_count = sum(
        1 for entry in value.entries.values() if entry.hmmm
    )
    return {
        "schema": SCHEMA,
        "version": VERSION,
        "entry_count": len(value.entries),
        "definition_receipt_count": len(value.definitions),
        "public_gonol_sha256": PUBLIC_GONOL_SHA256,
        "public_gonol_glyph_count": len(PUBLIC_GONOL_157),
        "public_gonol_hmmm_definition_count": public_gonol_hmmm_count,
        "public_gonol_glyph_definition_coverage": "complete",
        "character_receipts": [
            value.character_gonols[char].receipt_digest for char in sorted(value.character_gonols)
        ],
        "definition_receipts": [receipt.receipt_digest for receipt in value.definitions],
        "receipt_digest": value.receipt_digest,
    }


__all__ = [
    "CharacterDefinitionEntry",
    "CharacterDefinitionLayer",
    "PUBLIC_GONOL_157",
    "PUBLIC_GONOL_SHA256",
    "SCHEMA",
    "VERSION",
    "build_character_definition_layer",
    "character_layer_record",
    "load_character_definition_table",
]
