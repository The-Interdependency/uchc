# Hilbert inference migration contract

Status: **provisional, unimplemented UCHC migration target**. English remains
`extracted`; Stack owns this executable candidate and its public contract.
This document introduces no UCHC Hilbert API and claims no completed graduation.

## Exact producer and authority

[Stack PR #65](https://github.com/The-Interdependency/stack/pull/65) merged as
`6504ed963d93836f66fc88e354fe52809a1a3b7a`, containing reviewed candidate
`2a36a69c30a8395516cf6dc4ffae21ed9908e1bd`.

At that exact merged commit:

- [implementation](https://github.com/The-Interdependency/stack/blob/6504ed963d93836f66fc88e354fe52809a1a3b7a/research/english-gonol/english_gonol/hilbert_inference.py);
- [candidate contract and usage](https://github.com/The-Interdependency/stack/blob/6504ed963d93836f66fc88e354fe52809a1a3b7a/research/english-gonol/docs/hilbert-inference.md);
- [regression witnesses](https://github.com/The-Interdependency/stack/blob/6504ed963d93836f66fc88e354fe52809a1a3b7a/research/english-gonol/tests/test_hilbert_inference.py);
- [MIGRATION.json](https://github.com/The-Interdependency/stack/blob/6504ed963d93836f66fc88e354fe52809a1a3b7a/research/english-gonol/MIGRATION.json) records `extracted` and supersedes the false completed-graduation claim.

The [shared work graph](work-graphs/hilbert-inference.json) pins that merged
producer, the UCHC pre-repair baseline, UCNS, METAPAT, and the governing skill-lib.
Historical extraction and candidate-wheel identities in [MIGRATION.md](MIGRATION.md)
remain separate from this newer Hilbert implementation source identity.

## Domain-qualified claims

Each row is a separate domain claim. The following fields apply to **every row**:

- claiming domain: Stack English Gonol inference mathematics;
- scope: the exact Stack candidate above and this provisional migration description;
- status: `provisional` in UCHC; no ratification or implementation authority is granted here;
- authority source: the linked Stack candidate contract and implementation;
- effective version: Stack `6504ed963d93836f66fc88e354fe52809a1a3b7a`;
- supersedes: the unscoped UCHC wording in `7ab46c5df37fce9612eed9948fb4500f191f6746:docs/HILBERT_INFERENCE.md`, not upstream canon;
- downstream authorization: describe and compare the candidate; UCHC encoding remains pending migration and equivalence evidence.

The `term_id` values retain the producer's qualified identities. UCHC does not
create competing definitions by copying the terms.

| Surface / term_id | Claim type | Claimed sense and included uses | Excluded uses / neighboring claims | Unresolved |
| --- | --- | --- | --- | --- |
| Hilbert space / `stack.english-gonol.inference-math.hilbert-space` | borrowed | Abstract complete inner-product space over explicit `R` or `C`; bounded origin spaces are finite-dimensional. | UCNS carrier geometry, O/S/C channel tuple, renderer, or empirical inference quality. Machine floating-point arithmetic is not itself exact `R` or `C`. | Canonical scalar field; larger-scale completion. |
| basis / `stack.english-gonol.inference-math.basis` | specialized | Existing construct-qualified glyph, word, or definition axes form the origin-local basis. | Cartesian `x/y/z`, carrier position, sense label, or invented semantic coordinate. UCNS geometry remains separately owned. | Additional licensed origin bases. |
| Hilbert state vector / `stack.english-gonol.inference-math.vector` | borrowed | Mathematical element represented by sparse coefficients on one origin-local basis; Stack type `HilbertStateVector`. | METAPAT `Vector` that alters state, UCNS displacement vector, physical direction, or an inferred causal action. | No cross-domain equivalence is licensed. |
| inner product / `stack.english-gonol.inference-math.inner-product` | specialized | Origin-local orthonormal product, conjugate-linear on the left for `C`, with explicit field and construct identity. | Cross-origin angles, cross-artifact identity matching, semantic similarity, or probability. | Cross-origin geometry. |
| tensor product / `stack.english-gonol.inference-math.tensor-product` | borrowed | Ordered tensor-product basis factors preserving order and multiplicity; Stack `OrderedTensor` represents a basis ket. | METAPAT Tensor equivalence, bag-of-axes sum, concatenation as an algebraic law, arbitrary tensor superpositions, or a mandatory adjacent-scale ladder. | Licensed higher-scale composition and the input-frame bridge. |

### Collision record and provenance

Known overlapping vocabulary: mathematical vector/tensor, METAPAT Vector/Tensor,
and UCNS geometric vectors. Current METAPAT at
`1cdfb09dd00a451cee30eec2e78624df8c682662` distinguishes state, scalar measurement,
state-altering Vector, and resulting Transformation; its
[claims ledger](https://github.com/The-Interdependency/metapat/blob/1cdfb09dd00a451cee30eec2e78624df8c682662/docs/claims-ledger.md)
requires independent domain license rather than transfer by resemblance.

Collision result: **clear within this provisional scope by explicit
disambiguation**. `HilbertStateVector` denotes the mathematical element only;
`OrderedTensor` denotes the ordered mathematical basis ket only. Neither type
claims a METAPAT catalog binding or UCNS displacement law. Any future equivalence
or cross-domain mapping remains `hmmm` and must fail closed before encoding.

The operator's glyph-axis/closed-word-axis correction is recorded by the Stack
candidate. Its immutable public conversation identity remains `hmmm`; this
migration description does not manufacture ratification from that missing source.
No semantic, proof, certification, measurement, or empirical status transfers.

## Candidate construction to preserve

Admitted glyph axes form an origin-local orthonormal basis. A word's declared
ordered glyph references form its tensor basis state; closure promotes the word
to its already-declared word axis while preserving its lower-scale construction.
Definition promotion consumes its exact ordered closed word/glyph components.
Order, multiplicity, and the separate origins `O_G`, `O_W`, and `O_D(w)` survive.

The pinned Stack implementation provides `ConstructRef`, `VerifiedConstruct`,
`AxisRef`, `HilbertStateVector`, `OrderedTensor`, `AxisPromotion`,
`FiniteHilbertSpace`, and its axis/space/promotion helpers. It verifies artifact
bytes and logical receipt before consumption, derives factors from declared
character IDs, rejects non-finite inner products, and canonicalizes zero
coordinates. Word and definition dimensions use direct counts after verification.

Those names are **Stack-only candidate surfaces**. They are absent from the
UCHC package. Existing UCHC `inference_input.py` remains the receipt-bound input
reader documented in [INFERENCE_INPUT.md](INFERENCE_INPUT.md).

A future input-frame bridge must verify the frame's construct identity before
resolving IDs, preserve ordered word and whitespace-glyph occurrences, and require
an explicit scalar field. `frame_basis_state` is not implemented in either this
UCHC tree or the pinned Stack candidate. Its exact implementation and migration
replay remain `hmmm`; complete frame admission alone is not a Hilbert conversion.

O/S/C displacement and epicyclic paths remain downstream candidate readouts.
Their channel tuples do not define the language basis. No weights, phases,
probabilities, sense choices, or learned operators are supplied by this contract.

## Usage and verification

Use the existing [UCHC input API](INFERENCE_INPUT.md#usage-guidance). To inspect
or test the Hilbert candidate, use the exact Stack checkout, following its linked
usage guide. From that checkout:

```bash
test "$(git rev-parse HEAD)" = "6504ed963d93836f66fc88e354fe52809a1a3b7a"
cd research/english-gonol
python -m pytest -q tests/test_hilbert_inference.py
```

Migration is blocked by artifact/reference mismatch, glyph order or multiplicity
loss, Cartesian substitution, silent cross-origin/construct products, non-finite
arithmetic, inconsistent zero identity, unavailable API advertising, or a missing
exact producer pin. Preserve those falsifiers when migrating; preserve current
UCHC receipt behavior independently.

## Lifecycle and hmmm

No source is copied into UCHC by this contract update. Future migration must bind
an exact candidate, preserve tests and receipts, prove equivalence, verify the
same built artifact in a clean environment and Stack, publish verified bytes,
reconsume the released artifact, sever the ordinary forge implementation path,
and record the authorized scoped authority transition. Until then Stack remains
the implementation/public-contract owner.

`hmmm`: canonical `R`/`C`; cross-origin geometry; amplitude/phase; learned operators;
sense selection; sentence-axis and later promotion; input-frame bridge; immutable
public conversation identity; stable release, released-artifact reconsumption,
and scoped authority-transition receipt.
