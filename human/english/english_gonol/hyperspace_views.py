# === MODULE_BUILD ===
# id: english_gonol_hyperspace_views
#   module_name: hyperspace_views
#   module_kind: audit
#   summary: four candidate views over the hyperspace plus one differential synthesis; the pinned corpus adjudicates which views merit retainment
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, ViewError, word_views, run_view_adjudication
#   internal_surface: definition inner-product density, word-axis angle, provenance lift, canonical-witness lift, synthesis tuple, distinctness/collision counts
#   auth_boundary: none
#   storage_boundary: aggregate receipts only; per-word views recomputed on demand
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_hyperspace_views
#   rollout: four views plus synthesis; reality adjudicates retainment, not declaration
#   rollback: remove this module, facade exports, tests, and candidate documentation
#   requires: english_gonol_hyperspace_construct, english_gonol_hyperspace_geometry, ucns_lift_selection_candidates (via ucns source)
#   since: 2026-09-21
#   unresolved: view four reduces to derivation; views one, two, and three together are the thing
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: views_are_four_plus_synthesis
#   given: one word gonol
#   then: exactly four candidate views are produced together with one synthesis tuple, each construction-derived
#   class: correctness
#   since: 2026-09-21
#
# id: views_adjudication_counts_are_exact
#   given: a corpus sweep
#   then: per-view distinct-value and collision counts are exact integer counts over the swept words
#   class: correctness
#   since: 2026-09-21
#
# id: views_do_not_select
#   given: an adjudication report
#   then: the report ranks views by measured distinctness and never declares retainment
#   class: doctrine
#   since: 2026-09-21
# === END CONTRACTS ===

"""Four candidate views plus differential synthesis.

View 1: definition inner-product density (shared constituent axes).
View 2: word-axis angle (terminal glyph-walk NativeMobiusState).
View 3: provenance-interval lift (deck of the word id).
View 4: canonical-witness lift (constant per residue).

The synthesis is the canonical tuple of all four. The corpus adjudicates
which views merit retainment; this module never selects.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from fractions import Fraction
from pathlib import Path
from typing import Any

from .hyperspace_construct import HyperspaceError
from .hyperspace_geometry import (
    definition_inner_product,
    word_axis_angle,
)
from .motion_run import _load_verified_motion

SCHEMA = "english-gonol.hyperspace-views"
VERSION = "0.1.0"
_MODULUS = 157


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


def _definition_walk_state(
    db: sqlite3.Connection, word_id: int, build_motion: Any
) -> dict[str, Any] | None:
    rows = db.execute(
        "SELECT id, ordinal, definition_index FROM definitions "
        "WHERE origin_word_id = ? ORDER BY ordinal",
        (word_id,),
    ).fetchall()
    if not rows:
        return None
    walk = []
    for definition_id, ordinal, definition_index in rows:
        target = db.execute(
            "SELECT target_word_id FROM semantic_evidence "
            "WHERE definition_id = ? ORDER BY id LIMIT 1",
            (definition_id,),
        ).fetchone()
        semantic = target[0] if target else 0
        walk.append((ordinal, semantic, definition_index))
    motion = build_motion(tuple(walk))
    return {
        "definition_count": len(rows),
        "end_phase": f"{motion.end_phase.numerator}/{motion.end_phase.denominator}",
        "end_frame": motion.end_frame,
        "derivation": "terminal NativeMobiusState of the ordered definition walk",
    }


def word_views(
    db: sqlite3.Connection, word_id: int, ucns_source_root: Path
) -> dict[str, Any]:
    """Compute the four views and the synthesis tuple for one word."""

    angle = word_axis_angle(db, word_id, ucns_source_root)
    build_motion = _load_verified_motion(Path(ucns_source_root))
    definition_walk = _definition_walk_state(db, word_id, build_motion)
    phase_num = int(angle["end_phase"].split("/")[0])
    residue = phase_num % _MODULUS
    deck = word_id // _MODULUS

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
    view2 = {
        "glyph_walk": {"phase": angle["end_phase"], "frame": angle["end_frame"]},
        "definition_walk": definition_walk,
    }
    view3 = {"deck": deck, "residue": residue, "lift": deck * _MODULUS + residue}
    view4 = {
        "residue": residue,
        "lift": _MODULUS + residue,
        "derived": True,
        "derivation": (
            "157 + residue, where residue is the phase numerator mod 157 "
            "already carried by view2 and view3; view four reduces to derivation"
        ),
    }

    synthesis = (view1, view2, view3["lift"])
    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "word_id": word_id,
        "views": {
            "view1_definition_inner_product_density": view1,
            "view2_word_axis_angle": view2,
            "view3_provenance_interval_lift": view3,
            "view4_canonical_witness_lift": view4,
        },
        "synthesis": [
            view1,
            view2,
            view3["lift"],
        ],
        "synthesis_composition": "views one, two, and three together",
    }
    payload["receipt_sha256"] = _receipt(payload)
    return payload


def run_view_adjudication(
    state_dir: Path,
    ucns_source_root: Path,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    """Sweep the corpus and count each view's distinguishing power."""

    db = _open_db(state_dir)
    try:
        rows = db.execute("SELECT id FROM words ORDER BY id").fetchall()
        words = [row[0] for row in rows[:limit]] if limit is not None else [row[0] for row in rows]
        seen: dict[str, set[Any]] = {
            "view1_definition_inner_product_density": set(),
            "view2_word_axis_angle": set(),
            "view3_provenance_interval_lift": set(),
            "synthesis": set(),
        }
        collisions: dict[str, int] = {name: 0 for name in seen}
        view_names = [name for name in seen if name != "synthesis"]
        view4_values: set[str] = set()
        for word_id in words:
            record = word_views(db, word_id, ucns_source_root)
            for name in view_names:
                value = record["views"][name]
                key = json.dumps(value, sort_keys=True, separators=(",", ":"))
                if key in seen[name]:
                    collisions[name] += 1
                seen[name].add(key)
            view4_values.add(
                json.dumps(
                    record["views"]["view4_canonical_witness_lift"],
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            synthesis_key = json.dumps(
                record["synthesis"], sort_keys=True, separators=(",", ":")
            )
            if synthesis_key in seen["synthesis"]:
                collisions["synthesis"] += 1
            seen["synthesis"].add(synthesis_key)
    finally:
        db.close()

    ranking = sorted(
        (
            (name, len(values), collisions[name])
            for name, values in seen.items()
        ),
        key=lambda entry: (entry[1], -entry[2]),
        reverse=True,
    )

    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "word_count": len(words),
        "distinct_values": {name: len(values) for name, values in seen.items()},
        "collisions": collisions,
        "view4_canonical_witness_lift": {
            "derived": True,
            "distinct": len(view4_values),
            "note": "view four reduces to derivation; excluded from the synthesis",
        },
        "synthesis_composition": "views one, two, and three together",
        "ranking_by_distinctness": [
            {"view": name, "distinct": distinct, "collisions": collision}
            for name, distinct, collision in ranking
        ],
        "hmmm": (
            "view four reduces to derivation; views one, two, and three "
            "together are the thing. This report ranks, it does not select"
        ),
    }
    payload["receipt_sha256"] = _receipt(payload)
    return payload


class SynthesisRecord:
    """First-class synthesis of views one, two, and three for one word."""

    def __init__(
        self,
        word_id: int,
        surface: str,
        view1: dict[str, Any] | None,
        view2: dict[str, Any],
        view3: dict[str, Any],
        receipt_sha256: str,
    ) -> None:
        self.word_id = word_id
        self.surface = surface
        self.view1 = view1
        self.view2 = view2
        self.view3 = view3
        self.receipt_sha256 = receipt_sha256

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "version": VERSION,
            "word_id": self.word_id,
            "surface": self.surface,
            "view1": self.view1,
            "view2": self.view2,
            "view3": self.view3,
            "receipt_sha256": self.receipt_sha256,
        }

    def canonical_bytes(self) -> bytes:
        payload = self.as_dict()
        payload.pop("receipt_sha256", None)
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def receipt_bytes(self) -> bytes:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_synthesis_record(
    db: sqlite3.Connection, word_id: int, ucns_source_root: Path
) -> SynthesisRecord:
    """Build the first-class synthesis record for one word."""

    views = word_views(db, word_id, ucns_source_root)
    surface = db.execute(
        "SELECT surface FROM words WHERE id = ?", (word_id,)
    ).fetchone()[0]
    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "word_id": word_id,
        "surface": surface,
        "view1": views["views"]["view1_definition_inner_product_density"],
        "view2": views["views"]["view2_word_axis_angle"],
        "view3": views["views"]["view3_provenance_interval_lift"],
    }
    receipt = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return SynthesisRecord(
        word_id=word_id,
        surface=surface,
        view1=payload["view1"],
        view2=payload["view2"],
        view3=payload["view3"],
        receipt_sha256=receipt,
    )


def synthesis_corpus_receipt(
    state_dir: Path,
    ucns_source_root: Path,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    """Stream the full synthesis surface and return an aggregate receipt."""

    db = _open_db(state_dir)
    try:
        rows = db.execute("SELECT id FROM words ORDER BY id").fetchall()
        words = [row[0] for row in rows[:limit]] if limit is not None else [row[0] for row in rows]
        digest = hashlib.sha256()
        for word_id in words:
            record = build_synthesis_record(db, word_id, ucns_source_root)
            digest.update(record.receipt_bytes())
    finally:
        db.close()

    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "word_count": len(words),
        "limit": limit,
        "synthesis_composition": "views one, two, and three together",
        "hmmm": (
            "view four reduces to derivation; views one, two, and three "
            "together are the thing"
        ),
    }
    payload["receipt_sha256"] = hashlib.sha256(
        digest.digest()
        + json.dumps(
            {key: value for key, value in payload.items() if key != "receipt_sha256"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return payload


def verify_synthesis_replay(data: bytes, state_dir: Path, ucns_source_root: Path) -> dict[str, Any]:
    """Recompute the synthesis corpus receipt and verify byte-identically."""

    if not isinstance(data, bytes):
        raise ViewError("receipt must be bytes")
    try:
        obj = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ViewError("receipt is not valid canonical JSON") from exc
    if obj.get("schema") != SCHEMA or obj.get("version") != VERSION:
        raise ViewError("receipt schema or version mismatch")
    rebuilt = synthesis_corpus_receipt(state_dir, ucns_source_root, limit=obj.get("limit"))
    if rebuilt["receipt_sha256"] != obj.get("receipt_sha256"):
        raise ViewError("receipt digest does not match recomputation")
    rebuilt_bytes = json.dumps(rebuilt, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if rebuilt_bytes != data:
        raise ViewError("receipt does not replay byte-identically")
    return rebuilt


__all__ = [
    "SCHEMA",
    "VERSION",
    "ViewError",
    "word_views",
    "run_view_adjudication",
    "SynthesisRecord",
    "build_synthesis_record",
    "synthesis_corpus_receipt",
    "verify_synthesis_replay",
]
