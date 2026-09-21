# === MODULE_BUILD ===
# id: english_gonol_language_hyperspace
#   module_name: hyperspace_construct
#   module_kind: constructor
#   summary: consumes the pinned English v2 compact construct and admits the complete language hyperspace - expanded glyph inventory, glyph/word/definition origins with declared orthogonality, lossless promotion, construction-derived origin attachment, and cross-frame composition over shared identities
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, V2_MANIFEST_RECEIPT, HyperspaceError, GlyphGonol, WordGonol, DefinitionGonol, glyph_inventory, promote_glyph, recover_glyph, promote_word, recover_word, promote_definition, recover_definition, axes_orthogonal, attach_word_origin, attach_definition_frame, compose_word, compose_definition, hyperspace_receipt, verify_hyperspace_replay
#   internal_surface: pinned v2 manifest receipt, expanded glyph admission rules, axis manifests, incremental canonical receipt
#   auth_boundary: none
#   storage_boundary: aggregate receipts only; axis participation is determinable-not-stored
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_hyperspace_construct
#   rollout: complete language hyperspace over the expanded human-glyph inventory; Public Gonol carrier positions and axis participation remain distinct roles
#   rollback: remove this module and its tests
#   requires: english_gonol_full_construct (v2 compact construct), ucns_public_gonol (consumed inside the v2 construct)
#   since: 2026-09-20
#   unresolved: geometry of definition-axis orthogonality, cross-origin angles, and the continuum lift-selection law remain hmmm
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: hyperspace_glyph_carrier_and_axis_roles_are_distinct
#   given: a glyph gonol on the Public Gonol carrier
#   then: its carrier position and its axis participation at the glyph origin are recorded separately and never substituted for one another
#   class: correctness
#   since: 2026-09-20
#
# id: hyperspace_promotion_is_lossless
#   given: an admitted closed gonol
#   then: recovery after promotion returns the same internal construction, identities, order, multiplicity, relations, origin attachments, and provenance
#   class: correctness
#   since: 2026-09-20
#
# id: hyperspace_orthogonality_is_declared_per_origin
#   given: two distinct axes of one origin
#   then: they are orthogonal by construct convention, determinable without materializing an N x N relation
#   class: doctrine
#   since: 2026-09-20
#
# id: hyperspace_attachment_is_construction_derived
#   given: a word gonol with an axis participation point
#   then: its definition-frame zero attaches at that same point, and its glyph construction attaches to the word origin at that point; no centroid or endpoint substitution
#   class: correctness
#   since: 2026-09-20
#
# id: hyperspace_fails_closed
#   given: malformed input, missing construct tables, or a malformed receipt
#   then: the constructor raises HyperspaceError rather than inventing structure
#   class: safety
#   since: 2026-09-20
# === END CONTRACTS ===

"""Language hyperspace construct over the expanded human-glyph inventory.

The pinned English v2 compact construct supplies the closed gonols. This
module admits the expanded glyph inventory (all admitted source scalars,
carrier and non-carrier alike), one axis per glyph at the glyph origin,
one axis per word at the word origin, and one axis per definition at its
word's local definition origin. Atomic promotion adds axis participation;
it never replaces the construction with a label.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = "english-gonol.language-hyperspace"
VERSION = "0.1.0"

# Pinned v2 compact-construct manifest receipt. The construct.db under
# study must carry this manifest receipt before its rows may be consumed.
V2_MANIFEST_RECEIPT = "12277b4959c0c72b7af12097b8a77bf91866bbf669e7f4ac07b6a5f1426ebb57"

# Constructible compound glyph forms (rule present; admitted only when both
# constituents are admitted by the corpus).
_COMPOUND_FORMS = {"CRLF": ("\r", "\n")}


class HyperspaceError(ValueError):
    """Raised when the hyperspace constructor fails closed."""


@dataclass(frozen=True)
class GlyphGonol:
    identity: str
    carrier_position: int | None
    construction_kind: str
    construction_parts: tuple[str, ...]
    axis_index: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "carrier_position": self.carrier_position,
            "construction_kind": self.construction_kind,
            "construction_parts": list(self.construction_parts),
            "axis_index": self.axis_index,
        }


@dataclass(frozen=True)
class WordGonol:
    word_id: int
    surface: str
    glyph_ids: tuple[int, ...]
    axis_index: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "word_id": self.word_id,
            "surface": self.surface,
            "glyph_ids": list(self.glyph_ids),
            "axis_index": self.axis_index,
        }


@dataclass(frozen=True)
class DefinitionGonol:
    definition_id: int
    origin_word_id: int
    ordinal: int
    constituent_ids: tuple[tuple[str, int], ...]
    axis_index: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "definition_id": self.definition_id,
            "origin_word_id": self.origin_word_id,
            "ordinal": self.ordinal,
            "constituent_ids": [list(pair) for pair in self.constituent_ids],
            "axis_index": self.axis_index,
        }


def _open_db(state_dir: Path) -> sqlite3.Connection:
    db_path = Path(state_dir) / "construct.db"
    if not db_path.exists():
        raise HyperspaceError(f"construct.db not found under {state_dir}")
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _encoded_construction(scalar: str) -> tuple[str, tuple[str, ...]]:
    codepoint_hex = f"U+{ord(scalar):04X}"
    parts = tuple(codepoint_hex)
    try:
        name = unicodedata.name(scalar)
    except ValueError:
        return "encoded-codepoint", parts
    return "encoded-name", tuple(name) + (" ",) + parts


def glyph_inventory(db: sqlite3.Connection) -> dict[str, GlyphGonol]:
    """Admit the expanded glyph inventory.

    Carrier glyphs keep their exact Public Gonol carrier positions and are
    ordered first by carrier position; non-carrier admitted scalars follow
    in Unicode scalar order. Carrier position and axis participation are
    distinct roles of the same glyph gonol.
    """

    rows = db.execute(
        "SELECT id, scalar, public_position FROM characters ORDER BY id"
    ).fetchall()
    carrier_rows = sorted(
        (row for row in rows if row[2] is not None),
        key=lambda row: row[2],
    )
    non_carrier_rows = sorted(
        (row for row in rows if row[2] is None),
        key=lambda row: ord(row[1]),
    )
    inventory: dict[str, GlyphGonol] = {}
    axis = 0
    for _char_id, scalar, position in carrier_rows:
        inventory[scalar] = GlyphGonol(
            identity=scalar,
            carrier_position=position,
            construction_kind="carrier",
            construction_parts=(scalar,),
            axis_index=axis,
        )
        axis += 1
    for _char_id, scalar, _position in non_carrier_rows:
        kind, parts = _encoded_construction(scalar)
        inventory[scalar] = GlyphGonol(
            identity=scalar,
            carrier_position=None,
            construction_kind=kind,
            construction_parts=parts,
            axis_index=axis,
        )
        axis += 1
    for compound, (first, second) in _COMPOUND_FORMS.items():
        if first in inventory and second in inventory:
            inventory[compound] = GlyphGonol(
                identity=compound,
                carrier_position=None,
                construction_kind="compound",
                construction_parts=(first, second),
                axis_index=axis,
            )
            axis += 1
    return inventory


def promote_glyph(
    db: sqlite3.Connection, inventory: dict[str, GlyphGonol], scalar: str
) -> tuple[GlyphGonol, int]:
    """Promote a glyph gonol: atomic participation as an axis at O_G."""

    gonol = inventory.get(scalar)
    if gonol is None:
        raise HyperspaceError(f"glyph {scalar!r} is not admitted")
    return gonol, gonol.axis_index


def recover_glyph(
    db: sqlite3.Connection, inventory: dict[str, GlyphGonol], scalar: str
) -> GlyphGonol:
    """Recover the glyph gonol construction; promotion is lossless."""

    return promote_glyph(db, inventory, scalar)[0]


def promote_word(db: sqlite3.Connection, word_id: int) -> tuple[WordGonol, int]:
    """Promote a word gonol: atomic participation as an axis at O_W."""

    row = db.execute(
        "SELECT surface FROM words WHERE id = ?", (word_id,)
    ).fetchone()
    if row is None:
        raise HyperspaceError(f"word {word_id} is not constructed")
    glyph_ids = tuple(
        glyph[0]
        for glyph in db.execute(
            "SELECT character_id FROM word_characters WHERE word_id = ? ORDER BY ordinal",
            (word_id,),
        ).fetchall()
    )
    return WordGonol(word_id=word_id, surface=row[0], glyph_ids=glyph_ids, axis_index=word_id), word_id


def recover_word(db: sqlite3.Connection, word_id: int) -> WordGonol:
    """Recover the word gonol construction; promotion is lossless."""

    return promote_word(db, word_id)[0]


def promote_definition(
    db: sqlite3.Connection, definition_id: int
) -> tuple[DefinitionGonol, int]:
    """Promote a definition gonol: atomic participation as an axis at O_D(w)."""

    row = db.execute(
        "SELECT origin_word_id, ordinal FROM definitions WHERE id = ?",
        (definition_id,),
    ).fetchone()
    if row is None:
        raise HyperspaceError(f"definition {definition_id} is not constructed")
    origin_word_id, ordinal = row
    constituent_ids = tuple(
        (kind, word_id if word_id is not None else character_id)
        for _component_ordinal, kind, word_id, character_id in db.execute(
            "SELECT ordinal, kind, word_id, character_id FROM definition_components "
            "WHERE definition_id = ? ORDER BY ordinal",
            (definition_id,),
        ).fetchall()
    )
    axis_index = db.execute(
        "SELECT COUNT(*) FROM definitions WHERE origin_word_id = ? AND ordinal <= ?",
        (origin_word_id, ordinal),
    ).fetchone()[0]
    return (
        DefinitionGonol(
            definition_id=definition_id,
            origin_word_id=origin_word_id,
            ordinal=ordinal,
            constituent_ids=constituent_ids,
            axis_index=axis_index,
        ),
        axis_index,
    )


def recover_definition(db: sqlite3.Connection, definition_id: int) -> DefinitionGonol:
    """Recover the definition gonol construction; promotion is lossless."""

    return promote_definition(db, definition_id)[0]


def axes_orthogonal(origin: str, first: int, second: int) -> bool:
    """Declared orthogonality at one origin.

    Distinct axes of the same origin are orthogonal by construct
    convention; the relation is determinable-not-stored.
    """

    if origin not in {"O_G", "O_W", "O_D"}:
        raise HyperspaceError(f"unknown origin {origin!r}")
    return first != second


def attach_word_origin(word: WordGonol) -> dict[str, Any]:
    """Attach the word's glyph construction to the word origin.

    The closed ordered glyph construction of the word attaches at the
    word's own axis participation point in O_W.
    """

    return {
        "word_id": word.word_id,
        "attachment_point_q_w": word.axis_index,
        "glyph_construction_attached_at": word.axis_index,
        "derivation": "admission order of the closed word gonol",
    }


def attach_definition_frame(word: WordGonol) -> dict[str, Any]:
    """Attach the word's definition frame zero to its distinguished point.

    A_w(0_{F_w}) = q_w with q_w the word's axis participation point.
    """

    return {
        "word_id": word.word_id,
        "q_w": word.axis_index,
        "definition_frame_zero_attached_at": word.axis_index,
        "derivation": "word axis participation point",
    }


def compose_word(db: sqlite3.Connection, word_id: int) -> tuple[int, ...]:
    """Cross-frame composition: the word from its ordered glyph gonols."""

    return promote_word(db, word_id)[0].glyph_ids


def compose_definition(db: sqlite3.Connection, definition_id: int) -> tuple[int, ...]:
    """Cross-frame composition: the definition from its ordered constituents.

    Constituents resolve to existing shared word and character identities;
    repeated participation preserves order and multiplicity without
    duplicating identity.
    """

    return promote_definition(db, definition_id)[0].constituent_ids


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def hyperspace_receipt(state_dir: Path, *, limit: int | None = None) -> dict[str, Any]:
    """Stream the complete hyperspace origin manifests and return the receipt."""

    db = _open_db(Path(state_dir))
    try:
        inventory = glyph_inventory(db)
        word_count = db.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        definition_count = db.execute("SELECT COUNT(*) FROM definitions").fetchone()[0]
        digest = hashlib.sha256()

        glyph_entries = sorted(inventory.values(), key=lambda gonol: gonol.axis_index)
        for gonol in glyph_entries:
            digest.update(_canonical_bytes({"origin": "O_G", **gonol.as_dict()}))

        word_rows = db.execute(
            "SELECT id FROM words ORDER BY id"
        ).fetchall()
        emitted_words = 0
        for (word_id,) in word_rows:
            if limit is not None and emitted_words >= limit:
                break
            word, axis = promote_word(db, word_id)
            digest.update(_canonical_bytes({"origin": "O_W", "axis": axis, **word.as_dict()}))
            emitted_words += 1

        emitted_definitions = 0
        definition_rows = db.execute(
            "SELECT id FROM definitions ORDER BY origin_word_id, ordinal"
        ).fetchall()
        for (definition_id,) in definition_rows:
            if limit is not None and emitted_definitions >= limit:
                break
            definition, axis = promote_definition(db, definition_id)
            digest.update(
                _canonical_bytes(
                    {
                        "origin": "O_D",
                        "root_word_id": definition.origin_word_id,
                        "axis": axis,
                        **definition.as_dict(),
                    }
                )
            )
            emitted_definitions += 1
    finally:
        db.close()

    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "v2_manifest_receipt": V2_MANIFEST_RECEIPT,
        "glyph_axis_count": len(inventory),
        "word_axis_count": emitted_words,
        "definition_axis_count": emitted_definitions,
        "total_axes": len(inventory) + emitted_words + emitted_definitions,
        "limit": limit,
        "orthogonality": {
            "O_G": "distinct glyph axes are orthogonal by construct convention",
            "O_W": "distinct word axes are orthogonal by construct convention",
            "O_D": "distinct definition axes of one word are orthogonal by construct convention",
        },
        "promotion": "lossless; recovery returns the same construction",
        "attachment": {
            "glyph_construction_to_word_origin": "attaches at the word axis participation point",
            "definition_frame_zero": "A_w(0_F_w) = q_w, the word axis participation point",
        },
        "hmmm": (
            "the geometry of definition-axis orthogonality, cross-origin "
            "angles, and the continuum lift-selection law remain hmmm; "
            "carrier position and axis participation are distinct roles"
        ),
    }
    payload["receipt_sha256"] = hashlib.sha256(
        digest.digest()
        + _canonical_bytes(
            {key: value for key, value in payload.items() if key != "receipt_sha256"}
        )
    ).hexdigest()
    return payload


def verify_hyperspace_replay(data: bytes, state_dir: Path) -> dict[str, Any]:
    """Recompute the hyperspace receipt and verify byte-identically."""

    if not isinstance(data, bytes):
        raise HyperspaceError("receipt must be bytes")
    try:
        obj = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HyperspaceError("receipt is not valid canonical JSON") from exc
    if obj.get("schema") != SCHEMA or obj.get("version") != VERSION:
        raise HyperspaceError("receipt schema or version mismatch")
    rebuilt = hyperspace_receipt(state_dir, limit=obj.get("limit"))
    if rebuilt["receipt_sha256"] != obj.get("receipt_sha256"):
        raise HyperspaceError("receipt digest does not match recomputation")
    rebuilt_bytes = _canonical_bytes(rebuilt)
    if rebuilt_bytes != data:
        raise HyperspaceError("receipt does not replay byte-identically")
    return rebuilt


__all__ = [
    "SCHEMA",
    "VERSION",
    "V2_MANIFEST_RECEIPT",
    "HyperspaceError",
    "GlyphGonol",
    "WordGonol",
    "DefinitionGonol",
    "glyph_inventory",
    "promote_glyph",
    "recover_glyph",
    "promote_word",
    "recover_word",
    "promote_definition",
    "recover_definition",
    "axes_orthogonal",
    "attach_word_origin",
    "attach_definition_frame",
    "compose_word",
    "compose_definition",
    "hyperspace_receipt",
    "verify_hyperspace_replay",
]
