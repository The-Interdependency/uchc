"""Orthogonal unit-circle carrier sweep (experimental, v0).

Bounded English Gonol Construction experiment. It asks whether semantic
relationships between closed English word gonols are better represented by
``K = 1..7`` orthogonal unit-circle carriers, each able to hold its own
epicycles.

Strictly meaning-agnostic placement
-----------------------------------
No meaning is assigned to any carrier index beforehand. A carrier index is an
unnamed structural slot. Placement of a closed gonol onto a carrier and an
angle cell is derived deterministically from the gonol's ``atomic_id``
(SHA-256), so the policy is reproducible and meaning-agnostic. The gonol
identity itself is never replaced by the placement; the embedding binds
``source_id``, ``atomic_id``, and ``receipt_digest``.

What a carrier represents is therefore allowed to emerge from the evidence:
the sweep reports, for each carrier count, which primitives occupy which
carrier, and which semantic relation pairs stop colliding as carriers are
added. The experiment does not label the carriers.

Standing: implemented experimental candidate only. It does not establish
UCNS geometry, a lexical semantics, an embedding, or canon. See
``docs/orthogonal-carrier-sweep-v0.md``.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from english_gonol.gonol import construct_gonol

MAX_CARRIERS = 7
DEFAULT_ANGLE_CELLS = 16
DEFAULT_EPICYCLE_LEVELS = 1
SEED = "english-gonol.orthogonal-carrier-sweep/v0"

# Development fixture only. This is not OEWN evidence and is not a claim about
# English lexical truth. It provides a small relation set with enough
# collisions at low carrier counts for the sweep to measure.
_FIXTURE_WORDS: tuple[tuple[str, str], ...] = (
    # (source_id, surface)
    ("eg:w:big", "big"),
    ("eg:w:large", "large"),
    ("eg:w:small", "small"),
    ("eg:w:little", "little"),
    ("eg:w:fast", "fast"),
    ("eg:w:quick", "quick"),
    ("eg:w:slow", "slow"),
    ("eg:w:happy", "happy"),
    ("eg:w:glad", "glad"),
    ("eg:w:sad", "sad"),
    ("eg:w:unhappy", "unhappy"),
    ("eg:w:begin", "begin"),
    ("eg:w:start", "start"),
    ("eg:w:end", "end"),
    ("eg:w:finish", "finish"),
    ("eg:w:hot", "hot"),
    ("eg:w:cold", "cold"),
    ("eg:w:light", "light"),
    ("eg:w:dark", "dark"),
    ("eg:w:love", "love"),
    ("eg:w:hate", "hate"),
    ("eg:w:open", "open"),
    ("eg:w:close", "close"),
    ("eg:w:wet", "wet"),
    ("eg:w:dry", "dry"),
    ("eg:w:animal", "animal"),
    ("eg:w:dog", "dog"),
    ("eg:w:poodle", "poodle"),
    ("eg:w:cat", "cat"),
    ("eg:w:siamese", "siamese"),
    ("eg:w:vehicle", "vehicle"),
    ("eg:w:car", "car"),
    ("eg:w:sedan", "sedan"),
    ("eg:w:furniture", "furniture"),
    ("eg:w:chair", "chair"),
    ("eg:w:armchair", "armchair"),
    ("eg:w:plant", "plant"),
    ("eg:w:tree", "tree"),
    ("eg:w:oak", "oak"),
    ("eg:w:food", "food"),
    ("eg:w:fruit", "fruit"),
    ("eg:w:apple", "apple"),
    ("eg:w:person", "person"),
    ("eg:w:child", "child"),
    ("eg:w:toddler", "toddler"),
    ("eg:w:tool", "tool"),
    ("eg:w:hammer", "hammer"),
    ("eg:w:saw", "saw"),
    ("eg:w:wheel", "wheel"),
    ("eg:w:engine", "engine"),
    ("eg:w:branch", "branch"),
    ("eg:w:leaf", "leaf"),
    ("eg:w:body", "body"),
    ("eg:w:arm", "arm"),
    ("eg:w:leg", "leg"),
    ("eg:w:house", "house"),
    ("eg:w:room", "room"),
    ("eg:w:book", "book"),
    ("eg:w:page", "page"),
)

_FIXTURE_RELATIONS: tuple[tuple[str, str, str], ...] = (
    # (source_id, target_id, label)
    # synonyms
    ("eg:w:big", "eg:w:large", "synonym"),
    ("eg:w:small", "eg:w:little", "synonym"),
    ("eg:w:fast", "eg:w:quick", "synonym"),
    ("eg:w:happy", "eg:w:glad", "synonym"),
    ("eg:w:sad", "eg:w:unhappy", "synonym"),
    ("eg:w:begin", "eg:w:start", "synonym"),
    ("eg:w:end", "eg:w:finish", "synonym"),
    # antonyms
    ("eg:w:big", "eg:w:small", "antonym"),
    ("eg:w:fast", "eg:w:slow", "antonym"),
    ("eg:w:happy", "eg:w:sad", "antonym"),
    ("eg:w:begin", "eg:w:end", "antonym"),
    ("eg:w:hot", "eg:w:cold", "antonym"),
    ("eg:w:light", "eg:w:dark", "antonym"),
    ("eg:w:love", "eg:w:hate", "antonym"),
    ("eg:w:open", "eg:w:close", "antonym"),
    ("eg:w:wet", "eg:w:dry", "antonym"),
    # hypernym chains (depth 2)
    ("eg:w:animal", "eg:w:dog", "hypernym"),
    ("eg:w:dog", "eg:w:poodle", "hypernym"),
    ("eg:w:animal", "eg:w:cat", "hypernym"),
    ("eg:w:cat", "eg:w:siamese", "hypernym"),
    ("eg:w:vehicle", "eg:w:car", "hypernym"),
    ("eg:w:car", "eg:w:sedan", "hypernym"),
    ("eg:w:furniture", "eg:w:chair", "hypernym"),
    ("eg:w:chair", "eg:w:armchair", "hypernym"),
    ("eg:w:plant", "eg:w:tree", "hypernym"),
    ("eg:w:tree", "eg:w:oak", "hypernym"),
    ("eg:w:food", "eg:w:fruit", "hypernym"),
    ("eg:w:fruit", "eg:w:apple", "hypernym"),
    ("eg:w:person", "eg:w:child", "hypernym"),
    ("eg:w:child", "eg:w:toddler", "hypernym"),
    ("eg:w:tool", "eg:w:hammer", "hypernym"),
    ("eg:w:tool", "eg:w:saw", "hypernym"),
    # hyponym inverses (recursive reverse evidence)
    ("eg:w:poodle", "eg:w:dog", "hyponym"),
    ("eg:w:siamese", "eg:w:cat", "hyponym"),
    ("eg:w:sedan", "eg:w:car", "hyponym"),
    ("eg:w:armchair", "eg:w:chair", "hyponym"),
    ("eg:w:oak", "eg:w:tree", "hyponym"),
    ("eg:w:apple", "eg:w:fruit", "hyponym"),
    ("eg:w:toddler", "eg:w:child", "hyponym"),
    # meronyms
    ("eg:w:car", "eg:w:wheel", "meronym"),
    ("eg:w:car", "eg:w:engine", "meronym"),
    ("eg:w:tree", "eg:w:branch", "meronym"),
    ("eg:w:tree", "eg:w:leaf", "meronym"),
    ("eg:w:body", "eg:w:arm", "meronym"),
    ("eg:w:body", "eg:w:leg", "meronym"),
    ("eg:w:house", "eg:w:room", "meronym"),
    ("eg:w:book", "eg:w:page", "meronym"),
)


@dataclass(frozen=True, slots=True)
class PrimitiveEvidence:
    """One closed word gonol plus its fixture relations."""

    source_id: str
    surface: str
    gonol_id: str
    receipt_digest: str
    relations: tuple[tuple[str, str], ...]  # (target_source_id, label)


@dataclass(frozen=True, slots=True)
class CarrierSweepConfig:
    max_carriers: int = MAX_CARRIERS
    angle_cells: int = DEFAULT_ANGLE_CELLS
    epicycle_levels: int = DEFAULT_EPICYCLE_LEVELS
    seed: str = SEED


@dataclass(frozen=True, slots=True)
class CarrierRow:
    carriers: int
    primitives: int
    relations: int
    base_colliding_edges: int
    colliding_edges: tuple[tuple[str, str, str], ...]
    relation_pairs_resolved_at_this_k: tuple[tuple[str, str, str], ...]
    resolved_from_k1: int
    epicycle_edges: int
    epicycle_preserved_edges: int
    recursive_chains: int
    recursive_chains_preserved: int
    max_chain_epicycle_depth_needed: int
    carrier_occupancy: tuple[int, ...]
    carrier_entropy: float
    stable_rank: float
    marginal_rank_gain: float
    rank_gain_ratio: float


@dataclass(frozen=True, slots=True)
class CarrierSweepReport:
    schema: str
    version: str
    config: Mapping[str, Any]
    fixture: Mapping[str, Any]
    rows: tuple[CarrierRow, ...]
    first_zero_collision_carriers: int | None
    sustained_zero_collision_carriers: int | None
    smallest_useful_carriers: int | None
    diminishing_returns_carriers: int | None
    nonclaims: tuple[str, ...]
    hmmm: tuple[str, ...]
    report_digest: str


def _digest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _placement(atomic_id: str, carriers: int, angle_cells: int, seed: str) -> tuple[int, int]:
    """Meaning-agnostic placement: (carrier index, angle cell index).

    The carrier index and angle cell are derived from the closed gonol's
    SHA-256 atomic identity. No semantic label is attached to any carrier.
    """
    value = int(_digest(f"{seed}:{atomic_id}")[:16], 16)
    carrier = value % carriers
    angle_index = (value // carriers) % angle_cells
    return carrier, angle_index


def _angle_radians(angle_index: int, angle_cells: int) -> float:
    return (2.0 * math.pi * angle_index) / angle_cells


def _placement_vector(
    placement: tuple[int, int], carriers: int, angle_cells: int
) -> tuple[float, ...]:
    """Unit-circle placement as a real vector in ``R^{2*carriers}``.

    Carriers occupy disjoint orthogonal coordinate pairs. The vector length is
    exactly 1 and the pairwise dot product across different carriers is 0.
    """
    carrier, angle_index = placement
    theta = _angle_radians(angle_index, angle_cells)
    vector = [0.0] * (2 * carriers)
    vector[2 * carrier] = math.cos(theta)
    vector[2 * carrier + 1] = math.sin(theta)
    return tuple(vector)


def _stable_rank(vectors: Sequence[Sequence[float]]) -> float:
    """Stable rank ``||V||_F^4 / ||V^T V||_F^2`` computed without NumPy.

    This is a scale-free measure of how many genuinely independent directions
    the placement vectors use across the orthogonal carrier planes.
    """
    if not vectors:
        return 0.0
    dimension = len(vectors[0])
    gram = [[0.0] * dimension for _ in range(dimension)]
    for vector in vectors:
        for row in range(dimension):
            value_row = vector[row]
            if value_row == 0.0:
                continue
            for column in range(row, dimension):
                gram[row][column] += value_row * vector[column]
    gram_frobenius_squared = 0.0
    for row in range(dimension):
        for column in range(dimension):
            if column < row:
                value = gram[column][row]
            else:
                value = gram[row][column]
            gram_frobenius_squared += value * value
    frobenius_squared = float(len(vectors))
    if gram_frobenius_squared <= 0.0:
        return 0.0
    return (frobenius_squared * frobenius_squared) / gram_frobenius_squared


def _carrier_entropy(occupancy: Sequence[int]) -> float:
    total = sum(occupancy)
    if total <= 0:
        return 0.0
    maximum = math.log(max(1, len(occupancy)))
    if maximum <= 0.0:
        return 0.0
    entropy = 0.0
    for count in occupancy:
        if count <= 0:
            continue
        probability = count / total
        entropy -= probability * math.log(probability)
    return entropy / maximum


def load_development_fixture() -> tuple[PrimitiveEvidence, ...]:
    """Close every fixture word as a word gonol and attach its relations."""

    by_id: dict[str, PrimitiveEvidence] = {}
    for source_id, surface in _FIXTURE_WORDS:
        receipt = construct_gonol(scale="word", source=surface, source_id=source_id)
        by_id[source_id] = PrimitiveEvidence(
            source_id=source_id,
            surface=surface,
            gonol_id=receipt.gonol.atomic_id,
            receipt_digest=receipt.receipt_digest,
            relations=(),
        )
    grouped: dict[str, list[tuple[str, str]]] = {key: [] for key in by_id}
    for source_id, target_id, label in _FIXTURE_RELATIONS:
        if source_id not in by_id or target_id not in by_id:
            raise ValueError(f"fixture relation references unknown primitive: {source_id} -> {target_id}")
        grouped[source_id].append((target_id, label))
    return tuple(
        PrimitiveEvidence(
            source_id=item.source_id,
            surface=item.surface,
            gonol_id=item.gonol_id,
            receipt_digest=item.receipt_digest,
            relations=tuple(grouped[item.source_id]),
        )
        for item in (by_id[key] for key in sorted(by_id))
    )


def _relation_edges(
    primitives: Sequence[PrimitiveEvidence],
) -> tuple[tuple[PrimitiveEvidence, PrimitiveEvidence, str], ...]:
    by_id = {item.source_id: item for item in primitives}
    edges: list[tuple[PrimitiveEvidence, PrimitiveEvidence, str]] = []
    for source in primitives:
        for target_id, label in source.relations:
            edges.append((source, by_id[target_id], label))
    return tuple(edges)


def _hypernym_chains(
    primitives: Sequence[PrimitiveEvidence],
) -> tuple[tuple[PrimitiveEvidence, ...], ...]:
    """Chains of consecutive hypernym edges, used for recursion preservation."""

    by_id = {item.source_id: item for item in primitives}
    parents: dict[str, str] = {}
    for source in primitives:
        for target_id, label in source.relations:
            if label == "hypernym":
                parents[source.source_id] = target_id
    chains: list[tuple[PrimitiveEvidence, ...]] = []
    for source in primitives:
        chain = [source]
        cursor = source
        while cursor.source_id in parents:
            parent = by_id[parents[cursor.source_id]]
            chain.append(parent)
            cursor = parent
        if len(chain) > 1:
            chains.append(tuple(chain))
    return tuple(chains)


def _chain_epicycle_depth(
    chain: Sequence[PrimitiveEvidence],
    placements: Mapping[str, tuple[int, int]],
) -> int:
    """Maximum nested epicycle depth required to embed this chain.

    A base placement contributes depth 0. An edge whose child shares the
    parent's base cell requires one additional nested epicycle level at that
    edge, and later edges in the chain stack on top of it.
    """
    depth = 0
    running = 0
    for parent, child in zip(chain, chain[1:]):
        if placements[parent.source_id] == placements[child.source_id]:
            running += 1
        else:
            running = 0
        depth = max(depth, running)
    return depth


def _row(
    carriers: int,
    config: CarrierSweepConfig,
    primitives: Sequence[PrimitiveEvidence],
    edges: Sequence[tuple[PrimitiveEvidence, PrimitiveEvidence, str]],
    chains: Sequence[tuple[PrimitiveEvidence, ...]],
    previous_colliding: frozenset[tuple[str, str, str]] | None,
    k1_colliding: frozenset[tuple[str, str, str]],
) -> CarrierRow:
    placements = {
        item.source_id: _placement(item.gonol_id, carriers, config.angle_cells, config.seed)
        for item in primitives
    }
    occupancy = [0] * carriers
    for _carrier, _angle in placements.values():
        occupancy[_carrier] += 1

    colliding = []
    for source, target, label in edges:
        if placements[source.source_id] == placements[target.source_id]:
            colliding.append((source.surface, target.surface, label))
    colliding_set = frozenset(colliding)
    resolved = tuple(sorted(colliding_set - previous_colliding)) if previous_colliding is not None else ()
    resolved_from_k1 = len(k1_colliding - colliding_set)

    chain_depths = tuple(_chain_epicycle_depth(chain, placements) for chain in chains)
    preserved_chains = sum(
        1 for depth in chain_depths if depth <= config.epicycle_levels
    )

    vectors = [
        _placement_vector(placements[item.source_id], carriers, config.angle_cells)
        for item in primitives
    ]
    rank = _stable_rank(vectors)

    return CarrierRow(
        carriers=carriers,
        primitives=len(primitives),
        relations=len(edges),
        base_colliding_edges=len(colliding_set),
        colliding_edges=tuple(sorted(colliding_set)),
        relation_pairs_resolved_at_this_k=resolved,
        resolved_from_k1=resolved_from_k1,
        epicycle_edges=len(colliding_set),
        epicycle_preserved_edges=len(edges),
        recursive_chains=len(chains),
        recursive_chains_preserved=preserved_chains,
        max_chain_epicycle_depth_needed=max(chain_depths, default=0),
        carrier_occupancy=tuple(occupancy),
        carrier_entropy=_carrier_entropy(occupancy),
        stable_rank=rank,
        marginal_rank_gain=0.0,
        rank_gain_ratio=0.0,
    )


def run_sweep(
    primitives: Sequence[PrimitiveEvidence],
    config: CarrierSweepConfig | None = None,
) -> CarrierSweepReport:
    """Sweep carrier counts ``1..max_carriers`` and report the measured rows."""

    config = config or CarrierSweepConfig()
    if config.max_carriers < 1:
        raise ValueError("max_carriers must be at least 1")
    if config.angle_cells < 2:
        raise ValueError("angle_cells must be at least 2")

    edges = _relation_edges(primitives)
    chains = _hypernym_chains(primitives)

    def colliding_at(carriers: int) -> frozenset[tuple[str, str, str]]:
        placements = {
            item.source_id: _placement(item.gonol_id, carriers, config.angle_cells, config.seed)
            for item in primitives
        }
        return frozenset(
            (source.surface, target.surface, label)
            for source, target, label in edges
            if placements[source.source_id] == placements[target.source_id]
        )

    k1_colliding = colliding_at(1)
    previous: frozenset[tuple[str, str, str]] | None = None
    rows: list[CarrierRow] = []
    previous_rank = 0.0
    diminishing_returns: int | None = None
    for carriers in range(1, config.max_carriers + 1):
        row = _row(carriers, config, primitives, edges, chains, previous, k1_colliding)
        rows.append(row)
        previous = colliding_at(carriers)
        rank_gain = row.stable_rank - previous_rank
        rank_gain_ratio = rank_gain / 2.0 if carriers > 1 else 0.0
        row = CarrierRow(
            carriers=row.carriers,
            primitives=row.primitives,
            relations=row.relations,
            base_colliding_edges=row.base_colliding_edges,
            colliding_edges=row.colliding_edges,
            relation_pairs_resolved_at_this_k=row.relation_pairs_resolved_at_this_k,
            resolved_from_k1=row.resolved_from_k1,
            epicycle_edges=row.epicycle_edges,
            epicycle_preserved_edges=row.epicycle_preserved_edges,
            recursive_chains=row.recursive_chains,
            recursive_chains_preserved=row.recursive_chains_preserved,
            max_chain_epicycle_depth_needed=row.max_chain_epicycle_depth_needed,
            carrier_occupancy=row.carrier_occupancy,
            carrier_entropy=row.carrier_entropy,
            stable_rank=row.stable_rank,
            marginal_rank_gain=rank_gain,
            rank_gain_ratio=rank_gain_ratio,
        )
        rows[-1] = row
        previous_rank = row.stable_rank
        if diminishing_returns is None and carriers > 1 and rank_gain_ratio < 0.25:
            diminishing_returns = carriers

    zero_flags = tuple(row.base_colliding_edges == 0 for row in rows)
    first_zero = next(
        (row.carriers for row in rows if row.base_colliding_edges == 0), None
    )
    sustained_zero = None
    for index, flag in enumerate(zero_flags):
        if flag and all(zero_flags[index:]):
            sustained_zero = rows[index].carriers
            break
    smallest_useful = sustained_zero if sustained_zero is not None else first_zero

    nonclaims = (
        "no carrier index is assigned a semantic meaning",
        "not UCNS geometry canon",
        "not an English lexical truth claim",
        "not a word embedding",
        "not a measurement of semantic quality",
    )
    hmmm = (
        "what each carrier represents must emerge from evidence, not be imposed",
        "the angle-cell discretization is an experimental convenience, not a geometric law",
        "whether a larger OEWN-derived relation set changes the smallest useful carrier count",
    )
    report_payload = {
        "config": {
            "max_carriers": config.max_carriers,
            "angle_cells": config.angle_cells,
            "epicycle_levels": config.epicycle_levels,
            "seed": config.seed,
        },
        "fixture": {
            "primitives": len(primitives),
            "relations": len(edges),
            "recursive_chains": len(chains),
            "source": "development fixture; not OEWN evidence",
        },
        "rows": [asdict(row) for row in rows],
        "first_zero_collision_carriers": first_zero,
        "sustained_zero_collision_carriers": sustained_zero,
        "smallest_useful_carriers": smallest_useful,
        "diminishing_returns_carriers": diminishing_returns,
        "nonclaims": list(nonclaims),
        "hmmm": list(hmmm),
    }
    return CarrierSweepReport(
        schema="english-gonol.orthogonal-carrier-sweep",
        version="0.1.0",
        config=report_payload["config"],
        fixture=report_payload["fixture"],
        rows=tuple(rows),
        first_zero_collision_carriers=first_zero,
        sustained_zero_collision_carriers=sustained_zero,
        smallest_useful_carriers=smallest_useful,
        diminishing_returns_carriers=diminishing_returns,
        nonclaims=nonclaims,
        hmmm=hmmm,
        report_digest=_digest(
            json.dumps(report_payload, sort_keys=True, separators=(",", ":"))
        ),
    )


def report_json(report: CarrierSweepReport) -> str:
    """Deterministic JSON serialization of the report."""

    return json.dumps(
        {
            "schema": report.schema,
            "version": report.version,
            "config": dict(report.config),
            "fixture": dict(report.fixture),
            "rows": [asdict(row) for row in report.rows],
            "first_zero_collision_carriers": report.first_zero_collision_carriers,
            "sustained_zero_collision_carriers": report.sustained_zero_collision_carriers,
            "smallest_useful_carriers": report.smallest_useful_carriers,
            "diminishing_returns_carriers": report.diminishing_returns_carriers,
            "nonclaims": list(report.nonclaims),
            "hmmm": list(report.hmmm),
            "report_digest": report.report_digest,
        },
        indent=2,
        sort_keys=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=str, help="write JSON report to this path")
    args = parser.parse_args()
    report = run_sweep(load_development_fixture())
    payload = report_json(report)
    if args.out:
        from pathlib import Path

        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
