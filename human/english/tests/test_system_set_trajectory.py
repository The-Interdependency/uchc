# === CHECKS ===
# id: check_trajectory_order_multiplicity
#   proves: trajectory_preserves_order_and_multiplicity
#   call: self::test_order_and_multiplicity_are_load_bearing
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_trajectory_no_equivalence
#   proves: trajectory_does_not_assert_equivalence
#   call: self::test_same_signature_does_not_assert_equivalence
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_trajectory_origin_provenance
#   proves: trajectory_origin_is_explicit
#   call: self::test_ucns_input_preserves_identity_and_provenance
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from english_gonol.system_set_trajectory import SemanticStep, SystemSetTrajectory


def make(path_id, steps):
    return SystemSetTrajectory(
        construct_id="construct:english:v1",
        origin_id="origin:" + path_id,
        path_id=path_id,
        steps=tuple(steps),
        provenance_ids=("source:example",),
    )


def test_order_and_multiplicity_are_load_bearing():
    a = make("a", (
        SemanticStep("many", "relate", "system"),
        SemanticStep("system", "recurs", "system"),
        SemanticStep("system", "recurs", "system"),
    ))
    b = make("b", (
        SemanticStep("system", "recurs", "system"),
        SemanticStep("many", "relate", "system"),
        SemanticStep("system", "recurs", "system"),
    ))
    assert a.relation_signature != b.relation_signature
    assert a.receipt_sha256 != b.receipt_sha256


def test_same_signature_does_not_assert_equivalence():
    steps = (
        SemanticStep("agents", "compose", "population"),
        SemanticStep("population", "exhibits", "regularity"),
    )
    a = make("path-a", steps)
    b = make("path-b", steps)
    assert a.relation_signature == b.relation_signature
    for payload in (a.to_dict(), b.to_dict(), a.to_ucns_comparison_input()):
        assert "equivalent" not in payload
        assert "analogous" not in payload
        assert "recurrence" not in payload


def test_ucns_input_preserves_identity_and_provenance():
    trajectory = make("x", (SemanticStep("a", "r", "b"),))
    payload = trajectory.to_ucns_comparison_input()
    assert payload["origin_id"] == "origin:x"
    assert payload["path_id"] == "x"
    assert payload["structure_id"] == trajectory.receipt_sha256
    assert payload["provenance_ids"] == ["source:example"]
