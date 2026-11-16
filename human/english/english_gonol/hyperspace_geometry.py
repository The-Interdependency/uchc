# === MODULE_BUILD ===
# id: english_gonol_hyperspace_geometry_candidates
#   module_name: hyperspace_geometry
#   module_kind: candidate
#   summary: Measure the overlap between the constituent word sets of two definitions.
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, HyperspaceGeometryError, definition_inner_product, run_hyperspace_geometry_controls
#   internal_surface: constituent overlap and control cases
#   auth_boundary: none
#   storage_boundary: aggregate receipts only; per-word geometry recomputed on demand
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_hyperspace_geometry
#   rollout: verified English dictionary consumer
#   rollback: remove this module, facade exports, tests, and candidate documentation
#   requires: english_gonol_hyperspace_construct
#   since: 2026-09-21
#   unresolved: contextual sense selection
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: definition_inner_product_is_constructed_not_statistical
#   given: two definitions rooted at one word
#   then: count their shared distinct constituent word axes
#   class: correctness
# id: hyperspace_geometry_candidates_are_replayable
#   given: identical source records
#   then: replay the inner-product controls
#   class: correctness
# === END CONTRACTS ===
"""Measure the overlap between the constituent word sets of two definitions."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from .hyperspace_construct import promote_definition

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


def run_hyperspace_geometry_controls(
    state_dir: Path, ucns_source_root: Path | None = None
) -> dict[str, Any]:
    """Run the preregistered controls for the definition inner product."""

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

    finally:
        db.close()

    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "results": results,
        "survivors": [name for name, result in results.items() if result["ok"]],
        "selected": [],
        "hmmm": "the overlap counts shared constituent words",
    }
    payload["receipt_sha256"] = _receipt(payload)
    return payload
