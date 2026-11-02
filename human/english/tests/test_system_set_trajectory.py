# === CHECKS ===
# id: check_system_set_trajectory_order
#   proves: system_set_trajectory_preserves_order
#   call: self::test_order_and_multiplicity_are_load_bearing
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_system_set_trajectory_evidence
#   proves: system_set_trajectory_preserves_comparison_evidence
#   call: self::test_comparison_input_carries_complete_steps
#   requires: python3, git
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_system_set_trajectory_boundary
#   proves: system_set_trajectory_no_downstream_judgment
#   call: self::test_no_downstream_judgment_is_encoded
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_system_set_trajectory_immutable
#   proves: system_set_trajectory_immutable_inputs
#   call: self::test_mutable_inputs_are_frozen_before_identity
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import pytest

from english_gonol.system_set_trajectory import SCHEMA, VERSION, SemanticStep, SystemSetTrajectory


def make(path_id, steps):
    return SystemSetTrajectory(
        construct_id="english:construct:v2",
        origin_id="origin:" + path_id,
        path_id=path_id,
        steps=steps,
        provenance_ids=["source:fixture"],
    )


def test_order_and_multiplicity_are_load_bearing():
    a = make("a", [
        SemanticStep("many", "relate", "system"),
        SemanticStep("system", "recurs", "system"),
        SemanticStep("system", "recurs", "system"),
    ])
    b = make("a", [
        SemanticStep("system", "recurs", "system"),
        SemanticStep("many", "relate", "system"),
        SemanticStep("system", "recurs", "system"),
    ])
    assert a.relation_signature != b.relation_signature
    assert a.receipt_sha256 != b.receipt_sha256
    c = replace(a, steps=a.steps[:-1])
    for changed in (b, c):
        original = a.to_dict(include_receipt=False)
        variation = changed.to_dict(include_receipt=False)
        assert original.pop("steps") != variation.pop("steps")
        assert original == variation
        assert a.receipt_sha256 != changed.receipt_sha256


def test_comparison_input_carries_complete_steps():
    # Exact producer bytes are checked by tools/verify_package_extraction.py.
    t = make("x", [SemanticStep("axis:a", "rel:r", "axis:b")])
    payload = t.to_ucns_comparison_input()
    assert payload["construct_id"] == "english:construct:v2"
    assert payload["origin_id"] == "origin:x"
    assert payload["path_id"] == "x"
    assert payload["steps"] == [
        {"axis_id": "axis:a", "relation_id": "rel:r", "target_axis_id": "axis:b"}
    ]
    assert payload["provenance_ids"] == ["source:fixture"]
    assert payload["schema"] == SCHEMA
    assert payload["version"] == VERSION
    identity = payload.pop("structure_id")
    assert identity == sha256(json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")).hexdigest()
    for malformed in ([], (), [""], ["   "]):
        with pytest.raises(ValueError):
            replace(t, provenance_ids=malformed)


def test_no_downstream_judgment_is_encoded():
    forbidden = {"equivalence", "analogy", "equivalent", "analogous", "recurrence", "proof_status", "measurement"}
    for label in ("r", *sorted(forbidden)):
        trajectory = make("x", [SemanticStep("a", label, "b")])
        for payload in (trajectory.to_dict(), trajectory.to_ucns_comparison_input()):
            assert payload["schema"] == "english-gonol.system-set-trajectory"
            assert payload["steps"] == [{"axis_id": "a", "relation_id": label, "target_axis_id": "b"}]
            assert forbidden.isdisjoint(payload)
            assert forbidden.isdisjoint(payload["steps"][0])


def test_mutable_inputs_are_frozen_before_identity():
    steps = [SemanticStep("a", "r", "b")]
    provenance = ["source:fixture"]
    unresolved = ["closure hmmm"]
    t = SystemSetTrajectory("c", "o", "p", steps, provenance, unresolved)
    before = t.receipt_sha256
    steps.append(SemanticStep("b", "r", "c"))
    provenance.append("source:later")
    unresolved.append("later")
    assert t.receipt_sha256 == before
    assert len(t.steps) == 1
    assert t.provenance_ids == ("source:fixture",)
    assert t.unresolved == ("closure hmmm",)
    for field in ("steps", "provenance_ids", "unresolved"):
        for scalar in ("source:fixture", b"source:fixture", bytearray(b"source:fixture")):
            with pytest.raises(ValueError, match=field):
                replace(t, **{field: scalar})
        valid = getattr(t, field)
        for unordered in (set(valid), frozenset(valid), dict.fromkeys(valid)):
            with pytest.raises(ValueError, match=field):
                replace(t, **{field: unordered})
        with pytest.raises(ValueError, match=field):
            replace(t, **{field: iter(valid)})
