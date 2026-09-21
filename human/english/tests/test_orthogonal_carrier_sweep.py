from __future__ import annotations

import json
import math

from english_gonol.orthogonal_carrier_sweep import (
    _chain_epicycle_depth,
    _placement,
    _placement_vector,
    load_development_fixture,
    report_json,
    run_sweep,
)


def test_fixture_closes_word_gonols_with_known_relations() -> None:
    primitives = load_development_fixture()
    assert len(primitives) == 59
    by_id = {item.source_id: item for item in primitives}
    for item in primitives:
        assert len(item.gonol_id) == 64
        assert len(item.receipt_digest) == 64
        for target_id, label in item.relations:
            assert target_id in by_id
            assert label


def test_sweep_is_deterministic() -> None:
    first = run_sweep(load_development_fixture())
    second = run_sweep(load_development_fixture())
    assert first.report_digest == second.report_digest
    assert first.rows == second.rows


def test_collisions_resolve_as_carriers_grow() -> None:
    report = run_sweep(load_development_fixture())
    rows = {row.carriers: row for row in report.rows}
    assert rows[1].base_colliding_edges > 0
    assert rows[7].base_colliding_edges == 0
    assert rows[7].resolved_from_k1 == rows[1].base_colliding_edges
    assert report.first_zero_collision_carriers == 5
    assert report.sustained_zero_collision_carriers == 7
    assert report.smallest_useful_carriers == 7


def test_added_carriers_add_independent_structure() -> None:
    report = run_sweep(load_development_fixture())
    ranks = [row.stable_rank for row in report.rows]
    assert ranks == sorted(ranks)
    assert ranks[-1] > ranks[0]
    # A full new orthogonal circle adds up to two independent directions; the
    # measured gain per added carrier stays substantial through K=7.
    for row in report.rows[1:]:
        assert row.rank_gain_ratio >= 0.5


def test_placement_vectors_are_orthogonal_across_carriers() -> None:
    primitives = load_development_fixture()
    left = primitives[0]
    right = next(item for item in primitives if item.source_id != left.source_id)
    left_placement = _placement(left.gonol_id, carriers=7, angle_cells=16, seed="unit-test")
    right_placement = _placement(right.gonol_id, carriers=7, angle_cells=16, seed="unit-test")
    if left_placement[0] == right_placement[0]:
        return  # same carrier; orthogonality assertion not applicable to this pair
    left_vector = _placement_vector(left_placement, carriers=7, angle_cells=16)
    right_vector = _placement_vector(right_placement, carriers=7, angle_cells=16)
    dot = sum(a * b for a, b in zip(left_vector, right_vector, strict=True))
    assert math.isclose(dot, 0.0, abs_tol=1e-12)


def test_epicycles_preserve_fixture_recursive_chains() -> None:
    report = run_sweep(load_development_fixture())
    for row in report.rows:
        assert row.epicycle_preserved_edges == row.relations
        assert row.recursive_chains_preserved == row.recursive_chains
        assert row.max_chain_epicycle_depth_needed <= 1


def test_no_carrier_meaning_is_assigned_beforehand() -> None:
    report = run_sweep(load_development_fixture())
    payload = json.loads(report_json(report))
    assert "no carrier index is assigned a semantic meaning" in payload["nonclaims"]
    assert "meaning" not in payload["config"]
    for row in payload["rows"]:
        assert "carrier_labels" not in row
        assert "carrier_meaning" not in row


def test_chain_depth_counts_consecutive_collisions() -> None:
    class Node:
        def __init__(self, source_id: str) -> None:
            self.source_id = source_id

    chain = (Node("a"), Node("b"), Node("c"), Node("d"))
    placements = {
        "a": (0, 0),
        "b": (0, 0),  # collides with parent -> depth 1
        "c": (0, 0),  # consecutive collision -> depth 2
        "d": (1, 1),  # base-distinct -> resets
    }
    assert _chain_epicycle_depth(chain, placements) == 2
    assert _chain_epicycle_depth((Node("x"), Node("y")), {"x": (0, 0), "y": (0, 0)}) == 1
