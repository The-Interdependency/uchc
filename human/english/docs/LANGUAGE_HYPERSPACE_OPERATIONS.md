# Language Hyperspace Construct — Operations Specification

Status: specification only; not built.
Date: 2026-09-20

## Placement

The language hyperspace construct is the target. The app exposes it; the
animation does not define it. This document specifies the promotion,
origin-attachment, and composition operations together. A flat orthogonal
word basis alone does not fulfill this proposal.

Architectural placement is settled. The remaining specification concern is
how the three roles of one word identity compose and remain recoverable —
not whether the origins should be reduced to one flat space.

## Origins

Three origins exist. They are distinct. They connect only through the
shared identities of the gonols that occupy them; they are never merged.

1. **Glyph origin `O_G`** — the 157-axis construct carried by UCNS's exact
   Public Gonol. Each glyph is one axis, orthogonal to every other. Origin
   of all carrier geometry.
2. **Word origin `O_W`** — every word identity admitted by the closed
   current-corpus construct is one axis, orthogonal to every other. Axes
   are the constructed word identities, never a lookup vocabulary.
3. **Definition origin `O_D(w)`** — for each atomic word gonol `w`, its
   definitions `D1 .. Dn` are axes of a local origin, mutually orthogonal,
   with `w` as the origin gonol.

## The three capacities of one word identity

One word identity participates in three capacities. These are related roles
of the same gonol, not three disconnected representations:

- **A — constructed.** `w` is a closed construction of glyph axes at
  `O_G`: ordered glyph components, shared identity, multiplicity, and
  receipt-verifiable internal structure.
- **B — axis.** `w` is one orthogonal axis at `O_W`.
- **C — local origin.** `w` is the origin gonol of `O_D(w)`, its mutually
  orthogonal definitions.

Recoverability requirement: from any word identity, all three capacities
must be recoverable from the same gonol record.

## Operations

### 1. Promotion

`promote(w)`: the constructed word gonol `w` becomes an axis of `O_W`.

Preconditions:

- `w` is a closed gonol: admitted shared identity, complete internal glyph
  construction, occurrence references intact, receipt verified.
- The axis set of `O_W` is closed; promotion admits exactly the word
  identities of the pinned construct version. Open-class extension is a
  new origin version, never a silent axis.

Effects:

- `w` gains capacity B while retaining capacity A. Promotion adds the axis
  role; it does not move or dissolve the glyph construction.
- `w` becomes eligible for origin-attachment: `O_D(w)` becomes attachable.
- The word-axis manifest records: word identity, axis position, construct
  receipt, promotion receipt.

Not allowed:

- Promoting a word that is not yet a closed gonol.
- Promoting two axes for one word identity (one identity, one axis).
- Promoting from a table lookup or tokenizer output; promotion is from
  constructed structure only.

### 2. Origin-attachment

`attach(w, D_i)`: definition `D_i` of `w` becomes an axis of `O_D(w)`,
orthogonal to every other definition axis of `w`.

Preconditions:

- `w` is promoted (capacity B exists).
- `D_i` is a closed word-composition: every component word of `D_i` is a
  promoted axis at `O_W`; component order and provenance are recorded.
- The definition chain `w -> D1 -> D2 -> D3` and the direct relations
  `w -> D1`, `w -> D2`, `w -> D3` are preserved exactly.

Effects:

- `D_i` becomes an axis of `O_D(w)`.
- Mutual orthogonality of definition axes is declared by construct
  convention — the same convention as glyph orthogonality — never derived
  from statistical co-occurrence.
- Because `D_i` is composed of word identities, attachment reconnects
  `O_D(w)` to `O_W` through shared word identities: each definition axis
  contains word identities that are themselves axes at `O_W` with their
  own definition origins. This is the recursion.

Not allowed:

- Attaching a definition whose component words are not promoted.
- Deriving definition-axis orthogonality from frequencies, distances, or
  angles. Orthogonality is declared; evidence is measured elsewhere.

### 3. Composition

`compose(w, components)`: closes a gonol from its components.

Two levels:

- **Base composition.** `w` is composed of glyph components at `O_G`.
  Order, multiplicity, shared identity, and receipt are exact.
- **Recursive composition.** `D_i` is composed of word components. Each
  component is a word gonol carrying all three capacities. Composition
  therefore closes through shared identities: a definition of `w` reaches
  word axes of `O_W`, and each such word reaches its own `O_D`.

Effects:

- The composed gonol is atomic at its own scale: a word gonol participates
  atomically in its definitions; a definition participates atomically in
  its word's origin.
- Composition preserves order (ordinals), multiplicity (occurrence
  counts), relation (chain plus direct), provenance (sense and definition
  indices), and shared identity (references only; no duplication).

Not allowed:

- Tokens or AST nodes substituting for construction. They may verify only.
- Invented weights or proximities. Preserve shared sequences, words,
  positional characters, and non-positional characters separately; let the
  completed construct reveal their geometry.

## Recursion

The structure is recursive because definitions reconnect through shared
word identities:

```
O_G : glyph axes
O_W : word axes (each word a promoted closed glyph construction)
O_D(w) : definition axes of w, each a composition of word axes
         whose own O_D are reachable in turn
```

A flat orthogonal word basis fails this proposal precisely because it has
no local definition origins and no route from a definition back into the
word origin through shared identities.

## Receipt discipline

Each origin manifest — glyph, word, and definition — is canonical
serialized, hash-receipted, and byte-identical replayable. Tampering with
identity, relation, order, or provenance fails replay. Peak RAM is bounded
independently of corpus size; axes are accessed on demand, never
materialized as an N x N relation.

## hmmm

- Architectural placement is settled: the origins are not reduced to one
  flat space. Remaining concern: how the three roles compose and remain
  recoverable, specified above but not yet built.
- What orthogonality of definition axes does geometrically — angle,
  tangency, and proximity relations between `O_D(w)` axes and `O_W` axes —
  remains unresolved. The convention is declared; its geometric
  consequences are not yet derived.
- The 3-axis describing graph with evidence channels x, y, z remains
  external to every construct origin.
- The continuum lift-selection law remains hmmm.
