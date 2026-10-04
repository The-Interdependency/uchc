"""Ordered semantic trajectory boundary for UCHC.

UCHC owns semantic trajectory construction. UCNS owns structural comparison
evidence. METAPAT owns recurrence adjudication.
"""

# === MODULE_BUILD ===
# id: uchc_system_set_trajectory_v0
#   module_name: system_set_trajectory
#   module_kind: schema
#   summary: preserves ordered semantic trajectories for downstream structural comparison
#   owner: Erin Spencer
#   public_surface: SemanticStep, SystemSetTrajectory
#   internal_surface: receipt construction
#   auth_boundary: none
#   storage_boundary: serialization-only
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: human/english/tests/test_system_set_trajectory.py
#   rollout: candidate
#   rollback: remove module and tests
#   requires: existing UCHC axis identities
#   since: 2026-10-03
#   unresolved: automatic extraction from complete inference frames
# === END MODULE_BUILD ===

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

SCHEMA = "uchc.system-set-trajectory"
VERSION = "0.1.0"


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


@dataclass(frozen=True, slots=True)
class SemanticStep:
    axis_id: str
    relation_id: str
    target_axis_id: str

    def __post_init__(self):
        for value in (self.axis_id, self.relation_id, self.target_axis_id):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("semantic step fields must be non-empty strings")


@dataclass(frozen=True, slots=True)
class SystemSetTrajectory:
    construct_id: str
    origin_id: str
    path_id: str
    steps: tuple[SemanticStep, ...]
    provenance_ids: tuple[str, ...]
    unresolved: tuple[str, ...] = ()

    def __post_init__(self):
        for value in (self.construct_id, self.origin_id, self.path_id):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("trajectory identities must be non-empty strings")
        if not self.steps:
            raise ValueError("trajectory requires at least one step")

    @property
    def relation_signature(self):
        return tuple(step.relation_id for step in self.steps)

    @property
    def receipt_sha256(self):
        return sha256(_canonical(self.to_dict(include_receipt=False))).hexdigest()

    def to_dict(self, include_receipt=True):
        value = {
            "schema": SCHEMA,
            "version": VERSION,
            "construct_id": self.construct_id,
            "origin_id": self.origin_id,
            "path_id": self.path_id,
            "steps": [asdict(step) for step in self.steps],
            "provenance_ids": list(self.provenance_ids),
            "unresolved": list(self.unresolved),
        }
        if include_receipt:
            value["receipt_sha256"] = self.receipt_sha256
        return value

    def to_ucns_comparison_input(self):
        return {
            "origin_id": self.origin_id,
            "path_id": self.path_id,
            "structure_id": self.receipt_sha256,
            "provenance_ids": list(self.provenance_ids),
            "ordered_relation_signature": list(self.relation_signature),
            "unresolved": list(self.unresolved),
        }


__all__ = ["SCHEMA", "VERSION", "SemanticStep", "SystemSetTrajectory"]
