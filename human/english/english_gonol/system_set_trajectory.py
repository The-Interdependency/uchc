"""Stack-forged English semantic trajectory for structural recurrence research.

English Gonol Construction owns this provisional language trajectory while UCHC
graduation remains incomplete. UCNS owns structural comparison evidence.
METAPAT owns recurrence adjudication. EDCM owns measurement/evaluation.

Usage: construct SystemSetTrajectory with SemanticStep records and at least one
source provenance ID; call to_ucns_comparison_input() for the versioned handoff.
Recompute structure_id as SHA-256 of canonical JSON of all other handoff fields.
"""

# === MODULE_BUILD ===
# id: english_system_set_trajectory_v0
#   module_name: english_gonol.system_set_trajectory
#   module_kind: schema
#   summary: preserves ordered English semantic trajectories for downstream structural comparison
#   owner: Stack English Gonol Construction
#   public_surface: SemanticStep, SystemSetTrajectory
#   internal_surface: canonical receipt construction
#   auth_boundary: none
#   storage_boundary: serialization-only
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: research/english-gonol/tests/test_system_set_trajectory.py
#   rollout: stack-local research candidate
#   rollback: remove module and tests
#   requires: system-set provisional domain claim
#   since: 2026-10-03
#   unresolved: automatic extraction from complete sense-selected inference frames
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: system_set_trajectory_preserves_order
#   given: an ordered semantic trajectory is recorded
#   then: exact axis relation target order and multiplicity survive serialization and receipt identity
#   class: correctness
#
# id: system_set_trajectory_preserves_comparison_evidence
#   given: a trajectory is emitted for UCNS comparison
#   then: construct origin path complete ordered steps provenance and unresolved constraints remain inspectable
#   class: provenance_contract
#
# id: system_set_trajectory_no_downstream_judgment
#   given: trajectories expose matching or differing relation signatures
#   then: source relation labels remain unevaluated evidence in the English schema and assert no equivalence analogy recurrence proof or measurement outcome
#   class: boundary_contract
#
# id: system_set_trajectory_immutable_inputs
#   given: ordered sequence containers are passed by a caller
#   then: the record freezes them into tuples before identity is computed and rejects scalar or unordered containers
#   class: correctness
# === END CONTRACTS ===

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
import json

SCHEMA = "english-gonol.system-set-trajectory"
VERSION = "0.1.0"


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class SemanticStep:
    """A declared English relation, not a downstream adjudication.

    relation_id is an opaque source reference within this English schema.
    Even the label 'equivalence' records source evidence only; it does not
    evaluate the relation or assert UCNS structural equivalence.
    """

    axis_id: str
    relation_id: str
    target_axis_id: str

    def __post_init__(self) -> None:
        _text(self.axis_id, "axis_id")
        _text(self.relation_id, "relation_id")
        _text(self.target_axis_id, "target_axis_id")


@dataclass(frozen=True, slots=True)
class SystemSetTrajectory:
    construct_id: str
    origin_id: str
    path_id: str
    steps: tuple[SemanticStep, ...]
    provenance_ids: tuple[str, ...]
    unresolved: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.construct_id, "construct_id")
        _text(self.origin_id, "origin_id")
        _text(self.path_id, "path_id")
        for label in ("steps", "provenance_ids", "unresolved"):
            values = getattr(self, label)
            if isinstance(values, (str, bytes, bytearray)) or not isinstance(values, Sequence):
                raise ValueError(f"{label} must be an ordered sequence, not scalar text or an unordered collection")
            object.__setattr__(self, label, tuple(values))
        if not self.steps:
            raise ValueError("trajectory requires at least one semantic step")
        if any(not isinstance(step, SemanticStep) for step in self.steps):
            raise ValueError("steps must contain SemanticStep records")
        if not self.provenance_ids:
            raise ValueError("trajectory requires at least one provenance identifier")
        for label, values in (
            ("provenance_ids", self.provenance_ids),
            ("unresolved", self.unresolved),
        ):
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError(f"{label} must contain non-empty strings")

    @property
    def relation_signature(self) -> tuple[str, ...]:
        return tuple(step.relation_id for step in self.steps)

    @property
    def receipt_sha256(self) -> str:
        return sha256(_canonical(self.to_dict(include_receipt=False))).hexdigest()

    def to_dict(self, *, include_receipt: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
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

    def to_ucns_comparison_input(self) -> dict[str, object]:
        """Return identity-bearing evidence only; UCNS/METAPAT judge downstream."""

        value = self.to_dict(include_receipt=False)
        value["structure_id"] = self.receipt_sha256
        return value


__all__ = ["SCHEMA", "VERSION", "SemanticStep", "SystemSetTrajectory"]
