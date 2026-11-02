# === MODULE_BUILD ===
# id: english_gonol_hyperspace_geometry_candidates
#   module_name: hyperspace_geometry
#   module_kind: candidate
#   summary: preregistered candidates resolving two English hmmms - the constructed definition inner product (orthogonality from shared constituents) and the word-axis angle (terminal phase of the ordered glyph walk)
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, HyperspaceGeometryError, definition_inner_product, word_axis_angle, run_hyperspace_geometry_controls
#   internal_surface: shared-constituent intersection, glyph-walk motion over the selected lifted displacement, deterministic receipts
#   auth_boundary: none
#   storage_boundary: aggregate receipts only; per-word geometry recomputed on demand
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_hyperspace_geometry
#   rollout: candidate answers to English hmmm; survival is not selection
#   rollback: remove this module, facade exports, tests, and candidate documentation
#   requires: english_gonol_hyperspace_construct, english_gonol_motion_run (pinned ucns motion)
#   since: 2026-09-21
#   unresolved: candidates remain hmmm until preregistered controls pass and scoped selection receipts exist
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: definition_inner_product_is_constructed_not_statistical
#   given: two definitions of one word
#   then: the inner product equals the count of shared distinct constituent word axes, with disjoint definitions orthogonal by construction
#   class: correctness
#   since: 2026-09-21
#
# id: word_axis_angle_is_glyph_walk_terminal_phase
#   given: a word gonol with its ordered glyph construction
#   then: the word-axis angle candidate is the terminal NativeMobiusState of the glyph walk under the selected lifted displacement
#   class: correctness
#   since: 2026-09-21
#
# id: hyperspace_geometry_candidates_are_replayable
#   given: a candidate record
#   then: the canonical receipt replays deterministically and tampering fails closed
#   class: safety
#   since: 2026-09-21
# === END CONTRACTS ===

"""Candidate geometry for two English hmmms.

* H1-c4: the definition inner product counts shared distinct constituent
  word axes between two definitions of the same word; disjoint definitions
  are orthogonal by construction, and overlap is measured, not fitted.
* H2-c2: the word-axis angle is the terminal NativeMobiusState of the
  word's ordered glyph walk under the selected lifted ordered-concatenation
  displacement.

Candidates only; survival in the controls is not selection.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from .hyperspace_construct import HyperspaceError, promote_definition
from .motion_run import _load_verified_motion

SCHEMA = "english-gonol.hyperspace-geometry-candidates"
VERSION = "0.1.0"


class HyperspaceGeometryError(ValueError):
    """Raised when a hyperspace geometry candidate fails closed."""


def _open_db(state_dir: Path) -> sqlite3.Connection:
    db_path = Path(state_dir) / "construct.db"
    if not db_path.exists():
        raise HyperspaceGeometryError(f"construct.db not found under {state_dir}")
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _definition_word_axes(db: sqlite3.Connection, definition_id: int) -> set[int]:
    return {
        ref
        for kind, ref in db.execute(
            "SELECT kind, word_id FROM definition_components "
            "WHERE definition_id = ? AND kind = 'word'",
            (definition_id,),
        ).fetchall()
        if kind == "word" and ref is not None
    }


def _receipt(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def definition_inner_product(
    db: sqlite3.Connection, word_id: int, first: int, second: int
) -> dict[str, Any]:
    """The constructed inner product between two definitions of one word."""

    first_gonol = promote_definition(db, first)[0]
    second_gonol = promote_definition(db, second)[0]
    if first_gonol.origin_word_id != word_id or second_gonol.origin_word_id != word_id:
        raise HyperspaceGeometryError("both definitions must be rooted at the given word")
    first_axes = _definition_word_axes(db, first)
    second_axes = _definition_word_axes(db, second)
    shared = first_axes & second_axes
    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "candidate": "definition-inner-product",
        "word_id": word_id,
        "definition_ids": [first, second],
        "first_constituent_axes": sorted(first_axes),
        "second_constituent_axes": sorted(second_axes),
        "shared_constituent_axes": sorted(shared),
        "inner_product": len(shared),
        "norm_first": len(first_axes),
        "norm_second": len(second_axes),
        "orthogonal": len(shared) == 0,
        "derivation": "count of shared distinct constituent word axes",
    }
    payload["receipt_sha256"] = _receipt(payload)
    return payload


def word_axis_angle(
    db: sqlite3.Connection, word_id: int, ucns_source_root: Path
) -> dict[str, Any]:
    """The word-axis angle candidate: terminal phase of the glyph walk."""

    row = db.execute("SELECT surface FROM words WHERE id = ?", (word_id,)).fetchone()
    if row is None:
        raise HyperspaceGeometryError(f"word {word_id} is not constructed")
    glyph_rows = db.execute(
        "SELECT ordinal, character_id FROM word_characters WHERE word_id = ? ORDER BY ordinal",
        (word_id,),
    ).fetchall()
    if not glyph_rows:
        raise HyperspaceGeometryError(f"word {word_id} has no glyph construction")
    build_motion = _load_verified_motion(Path(ucns_source_root))
    walk = tuple((ordinal, character_id, 0) for ordinal, character_id in glyph_rows)
    motion = build_motion(walk)
    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "candidate": "word-axis-angle",
        "word_id": word_id,
        "surface": row[0],
        "glyph_walk": [[o, g, 0] for o, g in glyph_rows],
        "end_phase": f"{motion.end_phase.numerator}/{motion.end_phase.denominator}",
        "end_frame": motion.end_frame,
        "derivation": "terminal NativeMobiusState of the ordered glyph walk",
    }
    payload["receipt_sha256"] = _receipt(payload)
    return payload


def run_hyperspace_geometry_controls(
    state_dir: Path, ucns_source_root: Path
) -> dict[str, Any]:
    """Run the preregistered controls for both candidates."""

    db = _open_db(state_dir)
    try:
        results: dict[str, dict[str, Any]] = {}

        # inner-product controls
        inner_cases: dict[str, dict[str, Any]] = {}
        # self: norm equals distinct constituent count
        self_product = definition_inner_product(db, 1, 1, 1)
        inner_cases["self-norm"] = {
            "ok": self_product["inner_product"] == self_product["norm_first"],
            "detail": "inner product with itself equals its norm",
        }
        # disjoint: zero shared
        disjoint = definition_inner_product(db, 1, 1, 2)
        inner_cases["disjoint-orthogonal"] = {
            "ok": disjoint["orthogonal"] and disjoint["inner_product"] == 0,
            "detail": "disjoint definitions are orthogonal by construction",
        }
        # symmetry
        forward = definition_inner_product(db, 1, 1, 2)
        reverse = definition_inner_product(db, 1, 2, 1)
        inner_cases["symmetry"] = {
            "ok": forward["inner_product"] == reverse["inner_product"],
            "detail": "inner product is symmetric",
        }
        # shared: overlap measured, not fitted
        shared = definition_inner_product(db, 1, 1, 3)
        inner_cases["shared-overlap"] = {
            "ok": not shared["orthogonal"] and shared["inner_product"] > 0,
            "detail": f"shared overlap = {shared['inner_product']}",
        }
        inner_ok = all(case["ok"] for case in inner_cases.values())
        results["definition-inner-product"] = {
            "ok": inner_ok,
            "cases": inner_cases,
            "detail": "all preregistered inner-product controls pass" if inner_ok else "a control failed",
        }

        # word-axis-angle controls
        angle_cases: dict[str, dict[str, Any]] = {}
        first = word_axis_angle(db, 1, ucns_source_root)
        second = word_axis_angle(db, 1, ucns_source_root)
        angle_cases["determinism"] = {
            "ok": first["receipt_sha256"] == second["receipt_sha256"],
            "detail": "word-axis angle is deterministic",
        }
        other = word_axis_angle(db, 2, ucns_source_root)
        angle_cases["distinct-words-distinct-walks"] = {
            "ok": first["receipt_sha256"] != other["receipt_sha256"],
            "detail": "different glyph walks produce different records",
        }
        angle_ok = all(case["ok"] for case in angle_cases.values())
        results["word-axis-angle"] = {
            "ok": angle_ok,
            "cases": angle_cases,
            "detail": "all preregistered angle controls pass" if angle_ok else "a control failed",
        }
    finally:
        db.close()

    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "results": results,
        "survivors": [name for name, result in results.items() if result["ok"]],
        "selected": [],
        "hmmm": (
            "surviving controls do not select these candidates; scoped "
            "selection would require additional preregistered evidence"
        ),
    }
    payload["receipt_sha256"] = _receipt(payload)
    return payload


__all__ = [
    "SCHEMA",
    "VERSION",
    "HyperspaceGeometryError",
    "definition_inner_product",
    "word_axis_angle",
    "run_hyperspace_geometry_controls",
]
