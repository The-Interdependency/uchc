# === MODULE_BUILD ===
# id: english_gonol_describing_graph
#   module_name: describing_graph
#   module_kind: instrument
#   summary: the external 3-axis describing graph with evidence channels x, y, z; describes the construct from outside, shares no origin
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, DescribingGraphError, describe_word, describing_graph_receipt, verify_describing_graph_replay
#   internal_surface: residue channel extraction, external projection, streaming aggregate receipt
#   auth_boundary: none
#   storage_boundary: aggregate receipts only; projections recomputed on demand
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_describing_graph
#   rollout: external description instrument; never merged with any construct origin
#   rollback: remove this module, facade exports, tests, and candidate documentation
#   requires: english_gonol_full_construct (v2 compact construct)
#   since: 2026-09-23
#   unresolved: projection semantics are measurement only; the describing graph defines no construct geometry
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: describing_graph_is_external
#   given: a word gonol
#   then: the describing graph returns x, y, z residue projections and never claims membership in O_G, O_W, or O_D
#   class: doctrine
#   since: 2026-09-23
#
# id: describing_graph_channels_are_construction_derived
#   given: a word gonol
#   then: x is the word occurrence ordinal, y is the first semantic evidence target, and z is the definition count
#   class: correctness
#   since: 2026-09-23
#
# id: describing_graph_fails_closed
#   given: malformed input or a malformed receipt
#   then: the instrument raises DescribingGraphError rather than inventing coordinates
#   class: safety
#   since: 2026-09-23
# === END CONTRACTS ===

"""The external 3-axis describing graph.

Axes x, y, z are the three evidence residue channels. The graph describes
the construct from outside; it shares no origin with the glyph, word, or
definition origins.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = "english-gonol.describing-graph"
VERSION = "0.1.0"
_MODULUS = 157


class DescribingGraphError(ValueError):
    """Raised when the describing graph fails closed."""


def _open_db(state_dir: Path) -> sqlite3.Connection:
    db_path = Path(state_dir) / "construct.db"
    if not db_path.exists():
        raise DescribingGraphError(f"construct.db not found under {state_dir}")
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _receipt(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _semantic_map(db: sqlite3.Connection) -> dict[int, int]:
    """First semantic evidence target per definition, one linear scan."""

    targets: dict[int, int] = {}
    for definition_id, target_word_id in db.execute(
        "SELECT definition_id, target_word_id FROM semantic_evidence ORDER BY definition_id, id"
    ).fetchall():
        targets.setdefault(definition_id, target_word_id)
    return targets


def _first_definition_ids(db: sqlite3.Connection) -> dict[int, int]:
    """First definition id per origin word, one linear scan."""

    first: dict[int, int] = {}
    for definition_id, origin_word_id in db.execute(
        "SELECT id, origin_word_id FROM definitions ORDER BY origin_word_id, ordinal"
    ).fetchall():
        first.setdefault(origin_word_id, definition_id)
    return first


def describe_word(db: sqlite3.Connection, word_id: int) -> dict[str, Any]:
    """Project one word onto the external x, y, z residue channels."""

    row = db.execute("SELECT surface FROM words WHERE id = ?", (word_id,)).fetchone()
    if row is None:
        raise DescribingGraphError(f"word {word_id} is not constructed")
    definition_count = db.execute(
        "SELECT COUNT(*) FROM definitions WHERE origin_word_id = ?", (word_id,)
    ).fetchone()[0]
    first_definition_id = db.execute(
        "SELECT id FROM definitions WHERE origin_word_id = ? ORDER BY ordinal LIMIT 1",
        (word_id,),
    ).fetchone()
    semantic = 0
    if first_definition_id is not None:
        target = db.execute(
            "SELECT target_word_id FROM semantic_evidence WHERE definition_id = ? ORDER BY id LIMIT 1",
            (first_definition_id[0],),
        ).fetchone()
        semantic = target[0] if target else 0
    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "word_id": word_id,
        "surface": row[0],
        "x": word_id % _MODULUS,
        "y": semantic % _MODULUS,
        "z": definition_count % _MODULUS,
        "origin": "external describing graph; shares no origin with O_G, O_W, or O_D",
    }
    payload["receipt_sha256"] = _receipt(payload)
    return payload


def describing_graph_receipt(
    state_dir: Path, *, limit: int | None = None
) -> dict[str, Any]:
    """Stream the full describing graph and return the aggregate receipt."""

    db = _open_db(state_dir)
    try:
        rows = db.execute("SELECT id FROM words ORDER BY id").fetchall()
        words = [row[0] for row in rows[:limit]] if limit is not None else [row[0] for row in rows]
        semantic_map = _semantic_map(db)
        first_defs = _first_definition_ids(db)
        definition_counts = dict(
            db.execute(
                "SELECT origin_word_id, COUNT(*) FROM definitions GROUP BY origin_word_id"
            ).fetchall()
        )
        surfaces = dict(db.execute("SELECT id, surface FROM words").fetchall())
        digest = hashlib.sha256()
        x_sum = 0
        y_sum = 0
        z_sum = 0
        for word_id in words:
            definition_count = definition_counts.get(word_id, 0)
            semantic = semantic_map.get(first_defs.get(word_id, -1), 0)
            record = {
                "schema": SCHEMA,
                "version": VERSION,
                "word_id": word_id,
                "surface": surfaces.get(word_id),
                "x": word_id % _MODULUS,
                "y": semantic % _MODULUS,
                "z": definition_count % _MODULUS,
                "origin": "external describing graph; shares no origin with O_G, O_W, or O_D",
            }
            record["receipt_sha256"] = _receipt(record)
            x_sum += record["x"]
            y_sum += record["y"]
            z_sum += record["z"]
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
        "x_channel_sum": x_sum,
        "y_channel_sum": y_sum,
        "z_channel_sum": z_sum,
        "external": True,
        "hmmm": (
            "the describing graph projects the residue channels from outside; "
            "it defines no construct geometry and shares no origin"
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


def verify_describing_graph_replay(data: bytes, state_dir: Path) -> dict[str, Any]:
    """Recompute the describing graph receipt and verify byte-identically."""

    if not isinstance(data, bytes):
        raise DescribingGraphError("receipt must be bytes")
    try:
        obj = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DescribingGraphError("receipt is not valid canonical JSON") from exc
    if obj.get("schema") != SCHEMA or obj.get("version") != VERSION:
        raise DescribingGraphError("receipt schema or version mismatch")
    rebuilt = describing_graph_receipt(state_dir, limit=obj.get("limit"))
    if rebuilt["receipt_sha256"] != obj.get("receipt_sha256"):
        raise DescribingGraphError("receipt digest does not match recomputation")
    rebuilt_bytes = json.dumps(rebuilt, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if rebuilt_bytes != data:
        raise DescribingGraphError("receipt does not replay byte-identically")
    return rebuilt


__all__ = [
    "SCHEMA",
    "VERSION",
    "DescribingGraphError",
    "describe_word",
    "describing_graph_receipt",
    "verify_describing_graph_replay",
]
