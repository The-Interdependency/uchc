# === MODULE_BUILD ===
# id: english_gonol_hyperspace_views
#   module_name: hyperspace_views
#   module_kind: audit
#   summary: Describe pairwise overlap among the stored definitions of a word.
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, ViewError, word_views, run_view_adjudication
#   internal_surface: definition density and corpus count
#   auth_boundary: none
#   storage_boundary: aggregate receipts only; per-word views recomputed on demand
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_hyperspace_views
#   rollout: verified English dictionary consumer
#   rollback: remove this module, facade exports, tests, and candidate documentation
#   requires: english_gonol_hyperspace_geometry_candidates
#   since: 2026-09-21
#   unresolved: contextual sense selection
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: views_adjudication_counts_are_exact
#   given: stored definitions grouped by origin
#   then: report pairwise overlap and count distinct values across words
#   class: correctness
# === END CONTRACTS ===
"""Describe pairwise overlap among the stored definitions of a word."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from fractions import Fraction
from pathlib import Path
from typing import Any

from .hyperspace_geometry import definition_inner_product

SCHEMA = "english-gonol.hyperspace-views"
VERSION = "0.2.0"


class ViewError(ValueError):
    """Raised when a view computation fails closed."""


def _open_db(state_dir: Path) -> sqlite3.Connection:
    db_path = Path(state_dir) / "construct.db"
    if not db_path.exists():
        raise ViewError(f"construct.db not found under {state_dir}")
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _receipt(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _definition_density(
    db: sqlite3.Connection, word_id: int
) -> dict[str, Any] | None:
    definition_ids = [
        row[0]
        for row in db.execute(
            "SELECT id FROM definitions WHERE origin_word_id = ? ORDER BY ordinal",
            (word_id,),
        ).fetchall()
    ]
    if len(definition_ids) < 2:
        return None
    overlaps = []
    orthogonal_pairs = 0
    total_pairs = 0
    for i, first in enumerate(definition_ids):
        for second in definition_ids[i + 1 :]:
            product = definition_inner_product(db, word_id, first, second)
            overlaps.append(product["inner_product"])
            total_pairs += 1
            if product["orthogonal"]:
                orthogonal_pairs += 1
    return {
        "definition_count": len(definition_ids),
        "pair_count": total_pairs,
        "orthogonal_pair_count": orthogonal_pairs,
        "shared_sum": sum(overlaps),
        "density": Fraction(sum(overlaps), total_pairs) if total_pairs else Fraction(0),
    }


def word_views(
    db: sqlite3.Connection, word_id: int, ucns_source_root: Path | None = None
) -> dict[str, Any]:
    """Return definition overlap for one constructed word."""

    if db.execute("SELECT 1 FROM words WHERE id = ?", (word_id,)).fetchone() is None:
        raise ViewError(f"word {word_id} is not constructed")
    density = _definition_density(db, word_id)
    view1 = (
        {
            "definition_count": density["definition_count"],
            "pair_count": density["pair_count"],
            "orthogonal_pair_count": density["orthogonal_pair_count"],
            "shared_sum": density["shared_sum"],
        }
        if density is not None
        else None
    )
    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "word_id": word_id,
        "views": {"view1_definition_inner_product_density": view1},
    }
    payload["receipt_sha256"] = _receipt(payload)
    return payload


def run_view_adjudication(
    state_dir: Path, ucns_source_root: Path | None = None, *, limit: int | None = None,
) -> dict[str, Any]:
    """Count distinct definition-overlap records in corpus order."""

    db = _open_db(state_dir)
    try:
        rows = db.execute("SELECT id FROM words ORDER BY id").fetchall()
        words = rows[:limit]
        name = "view1_definition_inner_product_density"
        distinct = {
            json.dumps(word_views(db, word_id)["views"][name], sort_keys=True)
            for word_id, in words
        }
    finally:
        db.close()
    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "word_count": len(words),
        "distinct_values": {name: len(distinct)},
        "collisions": {name: len(words) - len(distinct)},
    }
    payload["receipt_sha256"] = _receipt(payload)
    return payload
