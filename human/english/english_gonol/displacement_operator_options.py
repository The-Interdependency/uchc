# === MODULE_BUILD ===
# id: english_gonol_displacement_operator_options
#   module_name: displacement_operator_options
#   module_kind: adjudication
#   summary: three channel-mapping options for D_O_W, adjudicated by identity preservation and displacement distinctness
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, DisplacementOperatorOptionsError, channel_option_a, channel_option_b, channel_option_c, apply_option_displacement, run_channel_option_adjudication
#   internal_surface: option builders, identity-preservation check, distinctness/collision counts, selection receipt
#   auth_boundary: none
#   storage_boundary: aggregate receipts only; per-word options recomputed on demand
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_displacement_operator_options
#   rollout: where options exist, build them; select what works by preserving the identity
#   rollback: remove this module, facade exports, tests, and candidate documentation
#   requires: english_gonol_displacement_operator, english_gonol_hyperspace_views
#   since: 2026-09-27
#   unresolved: selection is by the stated criterion (identity preservation, then distinctness), not by geometry preference
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: channel_options_are_built
#   given: one word gonol
#   then: exactly three channel-mapping options are available and each is construction-derived
#   class: correctness
#   since: 2026-09-27
#
# id: channel_option_selection_preserves_identity
#   given: a corpus sweep
#   then: an option is selected only if its channel tuple is injective over the swept words (zero channel collisions)
#   class: doctrine
#   since: 2026-09-27
#
# id: channel_option_selection_prefers_distinctness
#   given: two identity-preserving options
#   then: the option with more distinct displacement receipts is selected
#   class: doctrine
#   since: 2026-09-27
# === END CONTRACTS ===

"""Three channel-mapping options for the word displacement operator.

* option a: ordinal = word id, semantic = first semantic target, context =
  definition count (the current default);
* option b: ordinal = word id, semantic = glyph-walk terminal phase
  numerator, context = definition-walk terminal phase numerator;
* option c: ordinal = word id, semantic = definition inner-product
  shared_sum, context = definition count.

Selection preserves the identity: a channel tuple must be injective over
the corpus before distinctness is allowed to decide.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from .displacement_operator import (
    _channel_maps,
    _load_verified_ucns,
    _open_db,
)
from .hyperspace_views import _definition_density, word_views

SCHEMA = "english-gonol.displacement-operator-options"
VERSION = "0.1.0"
_MODULUS = 157


class DisplacementOperatorOptionsError(ValueError):
    """Raised when the option adjudication fails closed."""


def _receipt(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


_channel_maps_cache: dict[int, tuple[dict[int, str], dict[int, int], dict[int, int]]] = {}


def _cached_channel_maps(db: sqlite3.Connection) -> tuple[dict[int, str], dict[int, int], dict[int, int]]:
    key = id(db)
    if key not in _channel_maps_cache:
        _channel_maps_cache[key] = _channel_maps(db)
    return _channel_maps_cache[key]


def channel_option_a(db: sqlite3.Connection, word_id: int) -> tuple[int, int, int]:
    """Option a: ordinal, first semantic target, definition count."""

    _surfaces, counts, semantic_by_word = _cached_channel_maps(db)
    return word_id, semantic_by_word.get(word_id, 0), counts.get(word_id, 0)


def channel_option_b(db: sqlite3.Connection, word_id: int, ucns_source_root: Path) -> tuple[int, int, int]:
    """Option b: word id, glyph-walk phase numerator, definition-walk phase numerator."""

    views = word_views(db, word_id, ucns_source_root)
    view2 = views["views"]["view2_word_axis_angle"]
    glyph_num = int(view2["glyph_walk"]["phase"].split("/")[0])
    def_walk = view2["definition_walk"]
    def_num = int(def_walk["end_phase"].split("/")[0]) if def_walk else 0
    return word_id, glyph_num, def_num


def channel_option_c(db: sqlite3.Connection, word_id: int) -> tuple[int, int, int]:
    """Option c: word id, definition inner-product shared sum, definition count."""

    density = _definition_density(db, word_id)
    shared = density["shared_sum"] if density else 0
    count = density["definition_count"] if density else 0
    return word_id, shared, count


def apply_option_displacement(
    db: sqlite3.Connection,
    word_id: int,
    ucns_source_root: Path,
    option: str,
) -> dict[str, Any]:
    """Apply D_O_W with one named channel-mapping option."""

    if option == "a":
        channels = channel_option_a(db, word_id)
    elif option == "b":
        channels = channel_option_b(db, word_id, ucns_source_root)
    elif option == "c":
        channels = channel_option_c(db, word_id)
    else:
        raise DisplacementOperatorOptionsError(f"unknown option {option!r}")
    build_motion, build_lift = _load_verified_ucns(Path(ucns_source_root))
    motion = build_motion((channels,))
    phase_num = int(motion.end_phase.numerator)
    residue = phase_num % _MODULUS
    if residue == 0:
        lift_value = None
        lift_deck = None
    else:
        lift = build_lift(word_id, residue)
        lift_value = lift["lift"]
        lift_deck = word_id // _MODULUS
    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "option": option,
        "word_id": word_id,
        "channels": list(channels),
        "end_phase": f"{motion.end_phase.numerator}/{motion.end_phase.denominator}",
        "end_frame": motion.end_frame,
        "lift": lift_value,
        "lift_deck": lift_deck,
    }
    payload["receipt_sha256"] = _receipt(payload)
    return payload


def run_channel_option_adjudication(
    state_dir: Path,
    ucns_source_root: Path,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    """Build all options, then select by identity preservation and distinctness."""

    db = _open_db(state_dir)
    try:
        rows = db.execute("SELECT id FROM words ORDER BY id").fetchall()
        words = [row[0] for row in rows[:limit]] if limit is not None else [row[0] for row in rows]
        options: dict[str, dict[str, Any]] = {}
        for option in ("a", "b", "c"):
            channel_values: set[tuple[int, int, int]] = set()
            channel_collisions = 0
            receipts: set[str] = set()
            receipt_collisions = 0
            for word_id in words:
                record = apply_option_displacement(db, word_id, ucns_source_root, option)
                channels = tuple(record["channels"])
                if channels in channel_values:
                    channel_collisions += 1
                channel_values.add(channels)
                receipt = record["receipt_sha256"]
                if receipt in receipts:
                    receipt_collisions += 1
                receipts.add(receipt)
            options[option] = {
                "channel_collisions": channel_collisions,
                "distinct_channels": len(channel_values),
                "receipt_collisions": receipt_collisions,
                "distinct_receipts": len(receipts),
                "identity_preserved": channel_collisions == 0,
            }
    finally:
        db.close()

    identity_preserving = [
        name for name, stats in options.items() if stats["identity_preserved"]
    ]
    if identity_preserving:
        selected = max(
            identity_preserving,
            key=lambda name: (
                options[name]["distinct_receipts"],
                -options[name]["receipt_collisions"],
            ),
        )
    else:
        selected = None

    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "word_count": len(words),
        "options": options,
        "identity_preserving": identity_preserving,
        "selected": selected,
        "criterion": "identity preservation first, then distinctness",
        "hmmm": (
            "where options exist, build them; select what works by "
            "preserving the identity"
        ),
    }
    payload["receipt_sha256"] = _receipt(payload)
    return payload


__all__ = [
    "SCHEMA",
    "VERSION",
    "DisplacementOperatorOptionsError",
    "channel_option_a",
    "channel_option_b",
    "channel_option_c",
    "apply_option_displacement",
    "run_channel_option_adjudication",
]
