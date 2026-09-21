# === MODULE_BUILD ===
# id: english_gonol_motion_run
#   module_name: motion_run
#   module_kind: audit
#   summary: consumes the pinned UCNS motion candidate and runs definition-walk motions over the English v2 compact construct on demand; determinable-not-stored with an aggregate receipt
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, UCNS_MOTION_COMMIT, UCNS_MOTION_MODULE_SHA256, UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256, MotionRunError, run_definition_walk_motions, verify_motion_replay
#   internal_surface: verified ucns motion loading, definition-chain walk extraction, canonical aggregate receipt
#   auth_boundary: none
#   storage_boundary: aggregate receipt only; per-word motions are recomputed, never stored
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_motion_run
#   rollout: stack english-gonol audit of the ucns motion candidate; candidate standing, no selection claim
#   rollback: remove this module and its tests
#   requires: ucns_motion_candidate (pinned), english_gonol.full_construct_run (schema)
#   since: 2026-09-19
#   unresolved: motion selection follows displacement selection, which is unresolved
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: motion_run_binds_exact_ucns_motion_source
#   given: a ucns source root
#   then: only motion.py and visible_displacement.py bytes matching the pinned commit modules are consumed, else the run fails closed
#   class: correctness
#   since: 2026-09-19
#
# id: motion_run_recomputes_not_stores
#   given: a v2 construct state directory
#   then: per-word motions are recomputed from the definition walks and only the aggregate receipt is returned
#   class: doctrine
#   since: 2026-09-19
#
# id: motion_run_inherits_scoped_selected_status
#   given: the consumed ucns motion candidate
#   then: the aggregate receipt records the scoped-selection status of the lifted displacement
#   class: doctrine
#   since: 2026-09-20
# === END CONTRACTS ===

"""Run definition-walk motions over the English v2 construct.

Definition chain ``word -> D1 -> D2 -> D3`` becomes one motion walk: each
step carries (ordinal = definition ordinal, semantic = first semantic
evidence target word id, context = chain depth). Per-word motions are
recomputed on demand from the compact SQLite construct; only the aggregate
receipt is returned. The consumed UCNS motion candidate is UNSELECTED.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA = "english-gonol.definition-walk-motion"
VERSION = "0.1.0"

UCNS_MOTION_COMMIT = "1cf10c2df2541a332a77f2ed3feda0c6bef4abcc"
UCNS_MOTION_MODULE_SHA256 = "5fc2b40967ab9da9cc805935d169d04a4b09594267c16df9959e9a566aa6b541"
UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256 = "670c4e41f130b2d6b2439ee17c65bc699985d18e36d4958edbdb06e445c2c037"


class MotionRunError(ValueError):
    """Raised when the motion run fails closed."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_verified_motion(ucns_source_root: Path) -> Any:
    root = Path(ucns_source_root)
    motion = root / "src" / "ucns" / "motion.py"
    lifted = root / "src" / "ucns" / "lifted_displacement.py"
    if not motion.exists() or not lifted.exists():
        raise MotionRunError(f"ucns motion modules missing under {root}")
    if _sha256(motion) != UCNS_MOTION_MODULE_SHA256:
        raise MotionRunError("ucns motion.py bytes do not match the pinned commit")
    if _sha256(lifted) != UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256:
        raise MotionRunError("ucns lifted_displacement.py bytes do not match the pinned commit")
    try:
        subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", UCNS_MOTION_COMMIT, "HEAD"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        raise MotionRunError("ucns source root does not contain the pinned motion commit") from exc

    package = root / "src"
    sys.path.insert(0, str(package))
    try:
        from ucns.motion import build_motion  # type: ignore
    finally:
        sys.path.pop(0)
    return build_motion


def _definition_walks(db: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT d.origin_word_id, w.surface, d.id, d.ordinal, d.definition_index
        FROM definitions d
        JOIN words w ON w.id = d.origin_word_id
        ORDER BY d.origin_word_id, d.ordinal
        """
    ).fetchall()
    semantic_targets: dict[int, int] = {}
    for definition_id, target_word_id in db.execute(
        "SELECT definition_id, target_word_id FROM semantic_evidence ORDER BY definition_id, id"
    ).fetchall():
        semantic_targets.setdefault(definition_id, target_word_id)
    by_word: dict[int, dict[str, Any]] = {}
    for origin_word_id, surface, definition_id, ordinal, definition_index in rows:
        entry = by_word.setdefault(
            origin_word_id,
            {"word_id": origin_word_id, "surface": surface, "steps": []},
        )
        semantic = semantic_targets.get(definition_id, 0)
        entry["steps"].append(
            {
                "definition_id": definition_id,
                "ordinal": ordinal,
                "semantic": semantic,
                "depth": definition_index,
            }
        )
    return [entry for entry in by_word.values() if entry["steps"]]


def run_definition_walk_motions(
    state_dir: Path,
    ucns_source_root: Path,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    """Recompute definition-walk motions and return the aggregate receipt."""

    db_path = Path(state_dir) / "construct.db"
    if not db_path.exists():
        raise MotionRunError(f"construct.db not found under {state_dir}")
    build_motion = _load_verified_motion(Path(ucns_source_root))

    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        walks = _definition_walks(db)
    finally:
        db.close()

    words = []
    for entry in walks[:limit] if limit is not None else walks:
        walk = tuple(
            (step["ordinal"], step["semantic"], step["depth"])
            for step in entry["steps"]
        )
        motion = build_motion(walk)
        words.append(
            {
                "word_id": entry["word_id"],
                "surface": entry["surface"],
                "step_count": len(entry["steps"]),
                "motion_receipt": motion.receipt_sha256,
                "end_frame": motion.end_frame,
                "end_radius": repr(motion.end_radius),
            }
        )

    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "ucns_motion_commit": UCNS_MOTION_COMMIT,
        "ucns_motion_module_sha256": UCNS_MOTION_MODULE_SHA256,
        "ucns_lifted_displacement_module_sha256": UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256,
        "displacement_candidate": "lifted-ordered-concatenation",
        "displacement_candidate_status": "selected-scoped",
        "words": words,
        "word_count": len(words),
        "limit": limit,
        "hmmm": (
            "motion inherits the scoped selection of the lifted "
            "ordered-concatenation displacement; the continuum lift-selection "
            "law remains hmmm; per-word motions are recomputed, never stored"
        ),
    }
    payload["receipt_sha256"] = hashlib.sha256(
        json.dumps(
            {key: value for key, value in payload.items() if key != "receipt_sha256"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return payload


def verify_motion_replay(
    data: bytes,
    state_dir: Path,
    ucns_source_root: Path,
) -> dict[str, Any]:
    """Recompute the aggregate receipt and verify byte-identically."""

    if not isinstance(data, bytes):
        raise MotionRunError("receipt must be bytes")
    try:
        obj = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MotionRunError("receipt is not valid canonical JSON") from exc
    if obj.get("schema") != SCHEMA or obj.get("version") != VERSION:
        raise MotionRunError("receipt schema or version mismatch")
    rebuilt = run_definition_walk_motions(state_dir, ucns_source_root, limit=obj.get("limit"))
    if rebuilt["receipt_sha256"] != obj.get("receipt_sha256"):
        raise MotionRunError("receipt digest does not match recomputation")
    rebuilt_bytes = json.dumps(rebuilt, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if rebuilt_bytes != data:
        raise MotionRunError("receipt does not replay byte-identically")
    return rebuilt


__all__ = [
    "SCHEMA",
    "VERSION",
    "UCNS_MOTION_COMMIT",
    "UCNS_MOTION_MODULE_SHA256",
    "UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256",
    "MotionRunError",
    "run_definition_walk_motions",
    "verify_motion_replay",
]
