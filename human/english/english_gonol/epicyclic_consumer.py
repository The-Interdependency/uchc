# === MODULE_BUILD ===
# id: uchc_english_epicyclic_consumer
#   module_name: epicyclic_consumer
#   module_kind: adapter
#   summary: consumes the UCNS epicyclic graph over one sentence's full infer() bundles - every O x S x C connection becomes an edge that expands through space
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, UCNS_EPICYCLIC_COMMIT, UCNS_EPICYCLIC_GRAPH_MODULE_SHA256, UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256, UCNS_PLACEMENT_FRAME_MODULE_SHA256, EpicyclicConsumerError, build_sentence_epicyclic_graph, write_full_graph_record, read_full_graph_record
#   internal_surface: verified ucns consumption, infer() bundles, edge metadata, refused-connection accounting, byte-identical replay
#   auth_boundary: none
#   storage_boundary: immutable full-graph records only
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: tests.test_epicyclic_consumer
#   rollout: the epicyclic graph is the spatial structure; the admission cube remains admission inventory
#   rollback: remove this module and its tests
#   requires: uchc_english_inference_input, uchc_english_inference_v0, ucns_epicyclic_graph_candidate
#   since: 2026-09-30
#   unresolved: no harmonic substrate claim; selection follows preregistered controls
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: epicyclic_consumer_edges_are_bundles
#   given: one admitted sentence
#   then: every fired O x S x C bundle becomes exactly one expanding edge with its map_id and definition_id preserved
#   class: correctness
# id: epicyclic_consumer_refusals_are_named
#   given: bundles without receipts
#   then: refused connections are counted as named refusals and never become edges
#   class: correctness
# id: epicyclic_consumer_full_record_replays
#   given: a full graph record
#   then: the canonical record replays byte-identically and tampering fails closed
#   class: safety
# === END CONTRACTS ===
"""UCHC consumer of the UCNS epicyclic graph.

One sentence -> full infer() bundles -> one expanding edge per fired
connection, with map_id and definition_id preserved. Refused connections
are named refusals, never edges. The full graph record is the stored
object; a contracted phone card is allowed only after it exists.
"""

from __future__ import annotations

import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

from .inference_input import EnglishConstruct, InferenceFrame
from .inference_v0 import infer

SCHEMA = "uchc.english.epicyclic-consumer"
VERSION = "0.1.0"

UCNS_EPICYCLIC_COMMIT = "380ce7b7ec6b8b45ffa53ea4210070f0b3129747"
UCNS_EPICYCLIC_GRAPH_MODULE_SHA256 = "46369455490b61d083afb5652d10dee16bb01bd518254cc392805847692d13f4"
UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256 = "670c4e41f130b2d6b2439ee17c65bc699985d18e36d4958edbdb06e445c2c037"
UCNS_PLACEMENT_FRAME_MODULE_SHA256 = "27608365b9f42dbb59cd15c27525b697ca8cf33ad4f2b51db8a3b417b74c95e0"


class EpicyclicConsumerError(ValueError):
    """Raised when the consumer fails closed."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load_verified_ucns(root: Path) -> tuple[Any, Any]:
    root = Path(root)
    modules = (
        ("epicyclic_graph.py", UCNS_EPICYCLIC_GRAPH_MODULE_SHA256),
        ("lifted_displacement.py", UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256),
        ("placement_frame.py", UCNS_PLACEMENT_FRAME_MODULE_SHA256),
    )
    for name, digest in modules:
        path = root / "src" / "ucns" / name
        if not path.exists():
            raise EpicyclicConsumerError(f"ucns {name} missing under {root}")
        if _sha256(path) != digest:
            raise EpicyclicConsumerError(f"ucns {name} bytes do not match the pinned commit")
    try:
        subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor",
             UCNS_EPICYCLIC_COMMIT, "HEAD"],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        raise EpicyclicConsumerError("ucns checkout does not contain the pinned epicyclic commit") from exc
    package = root / "src"
    sys.path.insert(0, str(package))
    try:
        from ucns.epicyclic_graph import build_epicyclic_edge, build_epicyclic_graph  # type: ignore
    finally:
        sys.path.pop(0)
    return build_epicyclic_edge, build_epicyclic_graph


def build_sentence_epicyclic_graph(
    frame: InferenceFrame,
    corpus: EnglishConstruct,
    ucns_source_root: Path,
) -> dict[str, Any]:
    """One sentence -> one epicyclic graph over the full infer() bundles."""

    frame = frame.require_complete()
    build_edge, build_graph = _load_verified_ucns(Path(ucns_source_root))
    bundles = infer(frame, corpus, ucns_source_root)

    edges: list[dict[str, Any]] = []
    refusals: list[dict[str, str]] = []
    for bundle in bundles:
        if bundle.receipts is None:
            for refusal in bundle.refusals:
                refusals.append(
                    {"map_id": bundle.map_id,
                     "definition_id": bundle.definition_id,
                     "clause": refusal.clause}
                )
            continue
        o, s, c = bundle.channels
        edge = build_edge(o, s, c)
        edges.append({
            "map_id": bundle.map_id,
            "definition_id": bundle.definition_id,
            "edge": edge,
        })

    graph = build_graph([entry["edge"] for entry in edges])
    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "text": frame.text,
        "edge_count": len(edges),
        "edges": edges,
        "graph": graph,
        "refused_connections": refusals,
        "refused_count": len(refusals),
        "expansion_through_space": True,
        "hmmm": "connections expand through space; no scalar weight and no harmonic substrate is claimed",
    }
    payload["receipt_sha256"] = sha256(_canonical(payload)).hexdigest()
    return payload


def write_full_graph_record(payload: dict[str, Any], path: Path) -> Path:
    """Write the full graph record; this is the stored object."""

    path = Path(path)
    path.write_bytes(_canonical(payload))
    return path


def read_full_graph_record(data: bytes, ucns_source_root: Path) -> dict[str, Any]:
    """Recompute the full graph record and verify byte-identically."""

    if not isinstance(data, bytes):
        raise EpicyclicConsumerError("full graph record must be bytes")
    try:
        obj = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EpicyclicConsumerError("full graph record is not valid canonical JSON") from exc
    if obj.get("schema") != SCHEMA or obj.get("version") != VERSION:
        raise EpicyclicConsumerError("full graph record schema or version mismatch")
    for required in ("text", "edges", "refused_connections", "hmmm"):
        if required not in obj:
            raise EpicyclicConsumerError("full graph record is missing required fields")
    build_edge, build_graph = _load_verified_ucns(Path(ucns_source_root))
    rebuilt_edges = []
    try:
        for entry in obj["edges"]:
            edge = entry["edge"]
            connection = edge["connection"]
            rebuilt_edges.append({
                "map_id": entry["map_id"],
                "definition_id": entry["definition_id"],
                "edge": build_edge(connection[0], connection[1], connection[2],
                                   covering_degree=edge.get("covering_degree")),
            })
    except (KeyError, TypeError, IndexError) as exc:
        raise EpicyclicConsumerError("full graph record has a malformed edge") from exc
    graph = build_graph([entry["edge"] for entry in rebuilt_edges])
    rebuilt = {
        "schema": SCHEMA,
        "version": VERSION,
        "text": obj["text"],
        "edge_count": len(rebuilt_edges),
        "edges": rebuilt_edges,
        "graph": graph,
        "refused_connections": obj["refused_connections"],
        "refused_count": len(obj["refused_connections"]),
        "expansion_through_space": True,
        "hmmm": obj["hmmm"],
    }
    rebuilt["receipt_sha256"] = sha256(_canonical(rebuilt)).hexdigest()
    if rebuilt["receipt_sha256"] != obj.get("receipt_sha256"):
        raise EpicyclicConsumerError("full graph record receipt does not match recomputation")
    if _canonical(rebuilt) != data:
        raise EpicyclicConsumerError("full graph record does not replay byte-identically")
    return rebuilt


__all__ = [
    "SCHEMA",
    "VERSION",
    "UCNS_EPICYCLIC_COMMIT",
    "UCNS_EPICYCLIC_GRAPH_MODULE_SHA256",
    "UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256",
    "UCNS_PLACEMENT_FRAME_MODULE_SHA256",
    "EpicyclicConsumerError",
    "build_sentence_epicyclic_graph",
    "write_full_graph_record",
    "read_full_graph_record",
]
