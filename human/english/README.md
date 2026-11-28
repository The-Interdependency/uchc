## Ordinal disc stacks

Use [ordinal radius-halving](docs/halving.md) to construct words from Unicode
scalar bearings and stack the completed words at the next scale. Stack owns the
separate 16 b rad representation experiment.

## English numerology gonols

`english_gonol.numerology.Numerology` constructs one gonol per integer, glyph,
triangle or star on the 27-bearing English wheel. Integers retain their full
value at bearing `n % 27`. The recorded digits of 27 are `[1, 0]`, at
bearing zero. The front reads SPACE and a–z clockwise from the top.
The back capitalizes each glyph at the same bearing, including SPACE,
whose capital is the digit `0`.

A star is one equidistant field. At parent radius `R`, all its letters sit at
`R/2`, and the intrinsic distance between every two distinct letters is
`R/2`. Circular bearings show angular order. Straight chords in that
drawing have lengths determined by the angular gaps. The directed walk
sets the edge order, and its closing edge returns to the first vertex.

| Figure | Bearing order | Radius and distinct-pair distance |
| --- | --- | --- |
| Each of nine triangles | Start at the group number modulo 9. Advance 9 modulo 27. | `R` for all 3 |
| Each of three nine-point stars | Start at 0, 1 or 2. Advance 12 modulo 27. | `R/2` for all 9 |
| The 27-point star | Start at 0. Advance 13 modulo 27. | `R/2` for all 27 |

For example, `wheel.star(9, 1).distance("a", "p")` returns `R/2`.
To construct an explicit sequence of threes, `wheel.letter_trios("ajsbktclu")`
places **a j s** at `R`, **b k t** at `R/2`, and **c l u** at `R/4`.
SPACE and its capital occupy a slot whenever present. Each figure carries
its letter gonols, exact rays and directed endpoint bytes.
`wheel.replay(record)` reconstructs them at the same frame radius.
The profile uses the UCNS revision pinned by
`.[halving]`. After installing that extra, inspect a figure with
`python -m english_gonol.numerology --radius 1 star 9 --family 1`.

## Historical recursive attachment profile

Start with [recursive-stack.md](docs/recursive-stack.md) and the
[exact extraction receipt](experiments/recursive-attachment-v1/extraction.json).
Sentences stack closed words through the same native operation as glyphs within
words. Whole lexical ownership is represented by a typed source closure.
Bearing candidates remain explicit; historical ordinal/structural replay remains
available. Stack retains implementation authority pending graduation.

---
# English Gonol Construction

## Historical structural profile v1

The operator-ratified [structural profile](docs/structural-profile-v1.md) replaces
non-whitespace runs for that versioned corpus profile. It builds the complete pinned
corpus, keeps punctuation outside word identity, preserves ordered shared
participations, and exposes read-only query/replay through
`english_gonol.structural_query.StructuralField`. Start with the commands in
that document and the [exact input graph](docs/structural-profile-work-graph.json).
The v2 results below remain historical and are not receipts for the new profile.
Stack owns the implementation; UCHC carries the extracted candidate. Geometry,
compound lexical origins and graduation retain their explicit hmmm boundaries.


Extracted UCHC implementation copy: `human/english/`. Source:
`The-Interdependency/stack@ca190204de25de240662bb438af80c8dc405cea6`
(`research/english-gonol/`). The historical 2026-09-21 extraction reported
92 passing tests; current gate qualifications are in
[the migration record](../../docs/MIGRATION.md). Stack retains implementation
and public-contract authority until graduation completes.

## Authority

```text
METAPAT  -> affixiation semantics
UCNS     -> gonol / Public Gonol geometry
English  -> text admission and linguistic/semantic construction
EDCM     -> measurement/evaluation only
```

English construction consumes UCNS geometry; it does not invent geometry or
move English semantics into UCNS.

## Historical v2 invariants

```text
every admitted character is a gonol
one exact scalar  -> one shared character identity
one exact surface -> one shared word identity

glyph axes
  -> ordered glyph-axis construction
  -> closed word
  -> word axis
```

Once closed, a gonol is atomic at an admissible consuming scale. Reuse preserves
identity while order, multiplicity, relation, source position, and provenance
remain recoverable.

The Stack-owned Hilbert candidate uses admitted glyph and word axes as its
mathematical basis. This is an unimplemented UCHC migration target. This does not replace Public Gonol carrier
geometry with Cartesian coordinates. A word's ordered glyph-axis tensor remains
recoverable when the closed word promotes to its own word axis.

Corpus occurrences, sense ids, and synset ids are evidence/provenance, not
independent gonols. Definitions are word-anchored constructions: each retains
the shared word origin, exact ordered constituent word/whitespace-character
identities, source ordinal, direct binding, and chain predecessor.

See [`../../docs/HILBERT_INFERENCE.md`](../../docs/HILBERT_INFERENCE.md) for the
provisional migration contract and exact Stack producer identity.

## Full construct v2 — sealed historical profile

`english_gonol.full_construct_run` builds the complete pinned OEWN 2025 corpus
without promoting bookkeeping into geometry.

```text
word origin -> D1 -> D2 -> ... -> Dn     # chain topology
word origin -> D1, D2, ... Dn            # direct topology

ordinal evidence
+ semantic evidence
+ exact sentence-context evidence
-> preponderance relative to the rest of the sentence in which the word appears
-> hmmm until UCNS derives the displacement geometry
```

Definitions preserve their source exactly: every maximal non-whitespace run
reuses one shared word identity and every whitespace scalar reuses one shared
character identity. No normalization is applied.

The builder does not create sentence/sense/synset/n-gram singleton objects,
occurrence-object ledgers, closure graphs, synthetic relation circles,
tangencies, attention frames, or duplicate JSON copies of the database. It does
not synthesize weights, Cartesian coordinates, centers, radii, displacement
vectors, motion, or tangency.

The separate Stack Hilbert candidate forms mathematical basis vectors from the
axes already declared by the construction; it is not part of the UCHC package. Those basis vectors are not an
English-layer displacement law and do not assign geometric direction, distance,
weight, amplitude, or phase.

### Verified full-corpus result

Evidence is committed in `experiments/full-construct-v2/`.

- 118 shared character identities
- 164,864 shared word identities
- 1,739,949 ordered word-character references
- 185,155 word-anchored definitions
- 3,535,375 exact ordered definition components
- 866,183 resolved semantic evidence rows
- 0 unresolved semantic evidence rows
- SQLite integrity: `ok`
- logical receipt: `12277b4959c0c72b7af12097b8a77bf91866bbf669e7f4ac07b6a5f1426ebb57`
- generated database: 306,331,648 bytes
- build wall time: 1:34.79
- peak RSS: 286,692 KiB

The database itself remains generated state; the compact manifest, integrity
receipt, and resource receipt are committed.

## Run historical v2

```bash
python -m english_gonol.full_construct_run \
  --source-root /path/to/oewn-2025/src/yaml \
  --ucns-source-root /path/to/ucns \
  --out-dir experiments/full-construct-v2
```

Tests:

```bash
python -m pytest -q tests
```

See [`docs/full-construct-v2.md`](docs/full-construct-v2.md).

## Historical research

The orthogonal-carrier sweep and earlier definition-affixiation run remain
separate experiments and supply no placement law to v2. The falsified
`full_singleton_run.py` architecture and its UCNS singleton-axis support were
deleted rather than retained as an active precedent.

## hmmm

The exact UCNS law mapping ordinal + semantic + sentence-context evidence to
geometric displacement remains unresolved. The Hilbert basis does not settle
the canonical scalar field (`R` or `C`), cross-origin inner products,
amplitude/phase, learned operators, sense selection, or sentence-axis promotion.
No English-layer rule may fill those boundaries with invented weights,
directions, distances, Cartesian coordinates, centers, radii, tangencies, or
motion.
