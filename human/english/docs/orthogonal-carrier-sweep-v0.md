# Orthogonal unit-circle carrier sweep — v0

Status: `UNRESOLVED` experimental sweep. Standing: implemented experimental
candidate inside English Gonol Construction only. Nothing here is UCNS geometry
canon, an English lexical truth claim, a word embedding, or a measurement of
semantic quality.

## Question

Are semantic relationships between English primitives better represented by
`K = 1..7` orthogonal unit-circle carriers, each able to hold its own
epicycles?

Boundary rule followed: **no meaning is assigned to a carrier beforehand**.
Carrier indices are unnamed structural slots. A closed word gonol is placed by
a deterministic, meaning-agnostic policy derived from its `atomic_id`; the
gonol's `source_id`, `atomic_id`, and `receipt_digest` remain bound to the
placement, so the placement never substitutes for gonol identity.

## Method

1. Close each English primitive as a word gonol with
   `english_gonol.gonol.construct_gonol`.
2. For carrier count `K`, map each gonol to `(carrier, angle_cell)` via a
   seeded SHA-256 of `atomic_id`: `carrier = value % K`,
   `angle_cell = (value // K) % 16`. This policy is reproducible and uses no
   semantic information.
3. Count **colliding relation edges**: an edge `(source -> target, label)`
   collides when its two endpoint gonols share the same `(carrier, angle_cell)`.
4. Test **epicycles**: every colliding edge may attach the child as an epicycle
   of the parent; recursive hypernym chains are embedded and the maximum nested
   epicycle depth needed per chain is measured against the allowed level budget
   (default `1`).
5. Measure **independent structure**: each placement is a unit vector in
   `R^{2K}` using two orthogonal coordinates per carrier; the stable rank of
   the placement matrix measures how many independent directions the data
   actually uses, and per-carrier occupancy entropy measures how evenly the
   carriers are used.
6. Report `first_zero_collision_carriers`, `sustained_zero_collision_carriers`,
   and `smallest_useful_carriers` (the smallest `K` after which collisions stay
   zero through `K = 7`).

The source relation set is the module's development fixture (59 word gonols,
47 relation edges, 14 recursive hypernym chains). It is **not** OEWN evidence.

## Frozen run

- Module: `english_gonol.orthogonal_carrier_sweep`
- Receipt: [`../experiments/orthogonal-carrier-sweep-v0.json`](../experiments/orthogonal-carrier-sweep-v0.json)
- Replay:
  `python -m english_gonol.orthogonal_carrier_sweep --out /tmp/orthogonal-carrier-sweep-v0.json`

## Results

| K | colliding edges | resolved from K=1 | stable rank | rank gain ratio | chains preserved (L=1) | max chain epicycle depth |
|---|---|---|---|---|---|---|
| 1 | 3 | 0 | 1.97 | — | 14/14 | 1 |
| 2 | 3 | 0 | 3.70 | 0.866 | 14/14 | 1 |
| 3 | 2 | 1 | 5.75 | 1.026 | 14/14 | 1 |
| 4 | 3 | 0 | 6.77 | 0.510 | 14/14 | 1 |
| 5 | 0 | 3 | 9.14 | 1.186 | 14/14 | 0 |
| 6 | 2 | 1 | 10.14 | 0.500 | 14/14 | 1 |
| 7 | 0 | 3 | 11.78 | 0.819 | 14/14 | 0 |

Which semantic collisions occur and resolve:

- `K = 1..4`: `(cat, siamese, hypernym)`, `(siamese, cat, hyponym)`, and
  `(food, fruit, hypernym)` collide. These are the recursive hypernym-chain
  edges whose endpoints share a base cell.
- `K = 4`: `(food, fruit, hypernym)` resolves.
- `K = 5`: all three edges resolve (`first_zero_collision_carriers = 5`).
- `K = 6`: the `cat/siamese` pair re-collides under the meaning-agnostic
  policy (adding a carrier re-partitions all carriers, so resolution is not
  monotonic).
- `K = 7`: all three edges resolve again and stay resolved
  (`sustained_zero_collision_carriers = 7`).

## Findings

### 1. Which semantic collisions are resolved

On this fixture the only base collisions are the recursive hypernym/hyponym
pairs `cat/siamese` and `food/fruit`. Increasing from one carrier to seven
resolves all of them, but the meaning-agnostic placement is not monotonic:
`K = 6` reintroduces the `cat/siamese` collision even though `K = 5` was
collision-free. The smallest carrier count after which no collision reappears
through `K = 7` is **7**.

### 2. Whether epicycles preserve recursive relationships

Yes, on this fixture. Every colliding edge can be attached as an epicycle of
its parent, all 14 recursive hypernym chains are preserved at every carrier
count with the default one-level epicycle budget, and no chain needed more
than depth 1. Deeper recursion remains untested: the fixture only contains
depth-2 hypernym chains. The unit test
`test_chain_depth_counts_consecutive_collisions` pins the depth metric for
longer chains.

### 3. Whether added circles provide genuinely independent structure

Yes, structurally. Each added carrier contributes two orthogonal coordinates,
placement vectors on different carriers are orthogonal by construction, and
the measured stable rank grows with every added carrier
(`1.97 -> 3.70 -> 5.75 -> 6.77 -> 9.14 -> 10.14 -> 11.78`). No carrier count
in `1..7` shows diminishing returns by the chosen threshold (`rank_gain_ratio
< 0.25`): on this 59-primitive fixture all seven carriers remain structurally
used. This is capacity independence, not semantic independence — the placement
policy is meaning-agnostic, so the added circles decorrelate by spreading
primitives, not by discovering semantic axes.

### 4. Smallest useful number of carriers

- `first_zero_collision_carriers = 5`
- `sustained_zero_collision_carriers = 7`
- Reported `smallest_useful_carriers = 7` under the sustained-zero definition.

Interpretation: **5 carriers** are enough to make every relation edge
collision-free for this fixture, but **7 carriers** are the smallest count that
stays collision-free across the sweep under the meaning-agnostic policy.
Because the policy is not monotonic, "useful" must be defined as sustained
zero, not first zero.

## What the carriers look like (evidence only, no imposed meaning)

At `K = 7`, the meaning-agnostic placement produces these occupants:

- carrier 0: big, branch, dark, glad, love, oak, person, sedan, siamese
- carrier 1: car, child, finish, hate, hot, house, leaf, poodle, wheel
- carrier 2: body, cold, fruit, large, little, plant, small, start
- carrier 3: arm, armchair, begin, cat, chair, light, open, slow, vehicle
- carrier 4: animal, apple, fast, food, furniture, leg, quick, room, sad, saw, toddler, unhappy
- carrier 5: book, close, dog, tool, tree
- carrier 6: dry, end, engine, hammer, happy, page, wet

No semantic grouping emerges from the meaning-agnostic policy. That is the
expected null result for this policy and is recorded as evidence, not failure:
the carriers do structural separation work, and any semantic interpretation
would have to come from a later, meaning-aware placement policy — which this
experiment deliberately does not impose.

## hmmm

- What a carrier represents must emerge from evidence; the meaning-agnostic
  policy shows no emergent grouping, so the question is still open.
- Whether a larger OEWN-derived relation set changes the smallest useful
  carrier count.
- Whether deeper recursive chains (depth ≥ 3) exceed one epicycle level.
- Whether a meaning-aware placement policy would produce interpretable
  carriers, and whether that would be a legitimate construction or an imposed
  semantic prior.
- The angle-cell discretization (16 cells) is an experimental convenience,
  not a geometric law.
