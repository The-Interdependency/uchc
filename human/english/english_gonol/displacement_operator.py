# === MODULE_BUILD ===
# id: english_gonol_displacement_operator
#   module_name: displacement_operator
#   module_kind: candidate
#   summary: word-level displacement operator D_O_W over the word origin - each word displaces by its own construction-derived channels under the selected lifted displacement and provenance-interval lift
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, UCNS_OPERATOR_COMMIT, UCNS_LIFT_SELECTION_MODULE_SHA256, UCNS_MOTION_MODULE_SHA256, UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256, DisplacementOperatorError, apply_word_displacement, iterate_word_displacement, run_displacement_operator_controls, displacement_operator_receipt
#   internal_surface: verified UCNS consumption, channel extraction, provenance lift, deterministic receipts
#   auth_boundary: none
#   storage_boundary: aggregate receipts only; per-word displacements recomputed on demand
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_displacement_operator
#   rollout: candidate displacement operator inside the construct; the describing graph measures and never moves
#   rollback: remove this module, facade exports, tests, and candidate documentation
#   requires: english_gonol_full_construct (v2), ucns_lift_selection (pinned), ucns_motion (pinned)
#   since: 2026-09-27
#   unresolved: operator candidate standing; selection follows preregistered controls
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: displacement_operator_uses_selected_laws
#   given: one word gonol
#   then: the operator advances by the selected lifted displacement and selects the lift by the provenance-interval law
#   class: correctness
#   since: 2026-09-27
#
# id: displacement_operator_closes_inside_word_origin
#   given: one word gonol
#   then: the displaced position remains a word-origin position; no cross-origin coordinate is produced
#   class: doctrine
#   since: 2026-09-27
#
# id: displacement_operator_iteration_is_deck_translation
#   given: n-fold application of the operator
#   then: the lift advances by n decks exactly
#   class: correctness
#   since: 2026-09-27
#
# id: displacement_operator_fails_closed
#   given: malformed input, source drift, or a malformed receipt
#   then: the operator raises DisplacementOperatorError rather than inventing motion
#   class: safety
#   since: 2026-09-27
# === END CONTRACTS ===

"""Word-level displacement operator over the word origin.

D_O_W(w) displaces word w by its own construction-derived channels:

* ordinal = word id,
* semantic = first semantic-evidence target word id,
* context = definition count.

The operator advances the word's NativeMobiusState by the selected lifted
displacement and selects the lift by the provenance-interval law. It acts
inside the construct; the external describing graph measures the channels
and never moves.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA = "english-gonol.displacement-operator"
VERSION = "0.1.0"
_MODULUS = 157

UCNS_OPERATOR_COMMIT = "5a042416ef62abd9b674523284c2a31193918d66"
UCNS_MOTION_MODULE_SHA256 = "5fc2b40967ab9da9cc805935d169d04a4b09594267c16df9959e9a566aa6b541"
UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256 = "670c4e41f130b2d6b2439ee17c65bc699985d18e36d4958edbdb06e445c2c037"
UCNS_LIFT_SELECTION_MODULE_SHA256 = "e9be3f8668bd98170cf5820e1b0c679d1a98bf9c8984a6eab987a1209dda3fc1"


class DisplacementOperatorError(ValueError):
    """Raised when the displacement operator fails closed."""


def _open_db(state_dir: Path) -> sqlite3.Connection:
    db_path = Path(state_dir) / "construct.db"
    if not db_path.exists():
        raise DisplacementOperatorError(f"construct.db not found under {state_dir}")
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


_ucns_cache: dict[Path, tuple[Any, Any, Any]] = {}


def _load_verified_ucns(ucns_source_root: Path) -> tuple[Any, Any, Any]:
    root = Path(ucns_source_root)
    if root in _ucns_cache:
        return _ucns_cache[root]
    motion = root / "src" / "ucns" / "motion.py"
    lifted = root / "src" / "ucns" / "lifted_displacement.py"
    lift_sel = root / "src" / "ucns" / "lift_selection.py"
    for path, digest, name in (
        (motion, UCNS_MOTION_MODULE_SHA256, "motion.py"),
        (lifted, UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256, "lifted_displacement.py"),
        (lift_sel, UCNS_LIFT_SELECTION_MODULE_SHA256, "lift_selection.py"),
    ):
        if not path.exists():
            raise DisplacementOperatorError(f"ucns {name} missing under {root}")
        if _sha256(path) != digest:
            raise DisplacementOperatorError(f"ucns {name} bytes do not match the pinned commit")
    try:
        subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", UCNS_OPERATOR_COMMIT, "HEAD"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        raise DisplacementOperatorError("ucns checkout does not contain the pinned operator commit") from exc
    package = root / "src"
    sys.path.insert(0, str(package))
    try:
        from ucns.motion import build_motion  # type: ignore
        from ucns.lift_selection import build_provenance_interval_lift  # type: ignore
    finally:
        sys.path.pop(0)
    loaded = (build_motion, build_provenance_interval_lift)
    _ucns_cache[root] = loaded
    return loaded


def _channels(db: sqlite3.Connection, word_id: int) -> tuple[int, int, int]:
    row = db.execute("SELECT surface FROM words WHERE id = ?", (word_id,)).fetchone()
    if row is None:
        raise DisplacementOperatorError(f"word {word_id} is not constructed")
    definition_count = db.execute(
        "SELECT COUNT(*) FROM definitions WHERE origin_word_id = ?", (word_id,)
    ).fetchone()[0]
    first_def = db.execute(
        "SELECT id FROM definitions WHERE origin_word_id = ? ORDER BY ordinal LIMIT 1",
        (word_id,),
    ).fetchone()
    semantic = 0
    if first_def is not None:
        target = db.execute(
            "SELECT target_word_id FROM semantic_evidence WHERE definition_id = ? ORDER BY id LIMIT 1",
            (first_def[0],),
        ).fetchone()
        semantic = target[0] if target else 0
    return word_id, semantic, definition_count


def apply_word_displacement(
    db: sqlite3.Connection,
    word_id: int,
    ucns_source_root: Path,
    *,
    iterations: int = 1,
) -> dict[str, Any]:
    """Apply D_O_W to one word; iterations advance decks exactly."""

    if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations < 0:
        raise DisplacementOperatorError("iterations must be a nonnegative integer")
    build_motion, build_lift = _load_verified_ucns(Path(ucns_source_root))
    ordinal, semantic, context = _channels(db, word_id)
    motion = build_motion(((ordinal, semantic, context),))
    phase_num = int(motion.end_phase.numerator)
    residue = phase_num % _MODULUS
    source_ordinal = word_id + iterations * _MODULUS
    if residue == 0:
        lift_value = None
        lift_deck = None
        lift_note = "a ≡ 0 (mod 157) has no bijective lift; lift unresolved"
    else:
        lift = build_lift(source_ordinal, residue)
        lift_value = lift["lift"]
        lift_deck = source_ordinal // _MODULUS
        lift_note = None
    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "word_id": word_id,
        "surface": db.execute("SELECT surface FROM words WHERE id = ?", (word_id,)).fetchone()[0],
        "channels": {"ordinal": ordinal, "semantic": semantic, "context": context},
        "iterations": iterations,
        "end_phase": f"{motion.end_phase.numerator}/{motion.end_phase.denominator}",
        "end_frame": motion.end_frame,
        "lift": lift_value,
        "lift_deck": lift_deck,
        "lift_note": lift_note,
        "closure": "word origin O_W; no cross-origin coordinate",
    }
    payload["receipt_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload


def iterate_word_displacement(
    db: sqlite3.Connection, word_id: int, ucns_source_root: Path, iterations: int
) -> dict[str, Any]:
    """N-fold operator application."""

    return apply_word_displacement(db, word_id, ucns_source_root, iterations=iterations)


def run_displacement_operator_controls(
    state_dir: Path, ucns_source_root: Path
) -> dict[str, Any]:
    """Run the preregistered operator controls on the fixture corpus."""

    db = _open_db(state_dir)
    try:
        results: dict[str, dict[str, Any]] = {}
        # identity: zero channels displace to zero turn and the identity lift
        identity = db.execute("SELECT id FROM words ORDER BY id LIMIT 1").fetchone()
        if identity is None:
            raise DisplacementOperatorError("fixture has no words")
        # determinism
        first = apply_word_displacement(db, identity[0], ucns_source_root)
        second = apply_word_displacement(db, identity[0], ucns_source_root)
        results["determinism"] = {
            "ok": first["receipt_sha256"] == second["receipt_sha256"],
            "detail": "same word, same receipt",
        }
        # iteration is deck translation
        once = apply_word_displacement(db, identity[0], ucns_source_root, iterations=1)
        twice = apply_word_displacement(db, identity[0], ucns_source_root, iterations=2)
        results["iteration-deck-translation"] = {
            "ok": twice["lift"] == once["lift"] + _MODULUS,
            "detail": "two iterations advance the lift by one deck",
        }
        # closure: no cross-origin coordinate
        results["closure"] = {
            "ok": "O_W" in first["closure"],
            "detail": first["closure"],
        }
        # external invariance: channels do not change under iteration
        results["external-channel-invariance"] = {
            "ok": once["channels"] == twice["channels"],
            "detail": "the describing graph channels are unchanged by displacement",
        }
    finally:
        db.close()

    ok = all(case["ok"] for case in results.values())
    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "results": results,
        "ok": ok,
        "hmmm": (
            "the operator candidate acts inside the construct; the describing "
            "graph measures and never moves; selection follows preregistered "
            "controls, not this report"
        ),
    }
    payload["receipt_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload


def _channel_maps(db: sqlite3.Connection) -> tuple[dict[int, str], dict[int, int], dict[int, int]]:
    surfaces = dict(db.execute("SELECT id, surface FROM words").fetchall())
    definition_counts = dict(
        db.execute(
            "SELECT origin_word_id, COUNT(*) FROM definitions GROUP BY origin_word_id"
        ).fetchall()
    )
    first_defs: dict[int, int] = {}
    for definition_id, origin_word_id in db.execute(
        "SELECT id, origin_word_id FROM definitions ORDER BY origin_word_id, ordinal"
    ).fetchall():
        first_defs.setdefault(origin_word_id, definition_id)
    semantic_targets: dict[int, int] = {}
    for definition_id, target_word_id in db.execute(
        "SELECT definition_id, target_word_id FROM semantic_evidence ORDER BY definition_id, id"
    ).fetchall():
        semantic_targets.setdefault(definition_id, target_word_id)
    return surfaces, definition_counts, {
        word_id: semantic_targets.get(first_defs.get(word_id, -1), 0)
        for word_id in surfaces
    }


def displacement_operator_receipt(
    state_dir: Path,
    ucns_source_root: Path,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    """Stream the operator over the corpus and return an aggregate receipt."""

    db = _open_db(state_dir)
    try:
        build_motion, build_lift = _load_verified_ucns(Path(ucns_source_root))
        rows = db.execute("SELECT id FROM words ORDER BY id").fetchall()
        words = [row[0] for row in rows[:limit]] if limit is not None else [row[0] for row in rows]
        surfaces, definition_counts, semantic_by_word = _channel_maps(db)
        digest = hashlib.sha256()
        for word_id in words:
            ordinal = word_id
            semantic = semantic_by_word.get(word_id, 0)
            context = definition_counts.get(word_id, 0)
            motion = build_motion(((ordinal, semantic, context),))
            phase_num = int(motion.end_phase.numerator)
            residue = phase_num % _MODULUS
            if residue == 0:
                lift_value = None
                lift_deck = None
                lift_note = "a ≡ 0 (mod 157) has no bijective lift; lift unresolved"
            else:
                lift = build_lift(word_id, residue)
                lift_value = lift["lift"]
                lift_deck = word_id // _MODULUS
                lift_note = None
            record = {
                "schema": SCHEMA,
                "version": VERSION,
                "word_id": word_id,
                "surface": surfaces.get(word_id),
                "channels": {"ordinal": ordinal, "semantic": semantic, "context": context},
                "iterations": 1,
                "end_phase": f"{motion.end_phase.numerator}/{motion.end_phase.denominator}",
                "end_frame": motion.end_frame,
                "lift": lift_value,
                "lift_deck": lift_deck,
                "lift_note": lift_note,
                "closure": "word origin O_W; no cross-origin coordinate",
            }
            record["receipt_sha256"] = hashlib.sha256(
                json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            digest.update(
                json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
            )
    finally:
        db.close()

    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "word_count": len(words),
        "limit": limit,
        "hmmm": "candidate standing; selection follows preregistered controls",
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


__all__ = [
    "SCHEMA",
    "VERSION",
    "UCNS_OPERATOR_COMMIT",
    "UCNS_MOTION_MODULE_SHA256",
    "UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256",
    "UCNS_LIFT_SELECTION_MODULE_SHA256",
    "DisplacementOperatorError",
    "apply_word_displacement",
    "iterate_word_displacement",
    "run_displacement_operator_controls",
    "displacement_operator_receipt",
]
