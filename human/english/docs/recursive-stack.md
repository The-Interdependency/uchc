# Recursive attachment profile

GPT generated; context, prompt Erin Spencer.

`english.attachment/1` applies the same native UCNS stack to glyphs within words
and closed words within sentences. Compound joining is a separate native rigid
attachment: it preserves the components' local radii and retains their boundary.
The declared `bull + shit` join attaches at the second `l`; the resulting closed
compound can itself participate in a parent stack.

Stack owns English admission and source relations. UCNS owns all geometry.
UCHC must extract this source and tests at an exact Stack commit. The
[input work graph](recursive-work-graph.json) records the starting baselines;
its Stack baseline is not the eventual extraction commit. Graduation is unchanged.

## Exact construction and views

With `n` participants, occurrence `i` has depth `n-i`, radius `R/2**(n-i)` and
the previous placed heading as its SPACE direction. Its origin is the preceding
endpoint. Appending halves the earlier parent geometry and advances disk depths.
Closed interiors keep their own local geometry, order, repeated occurrences and
source identities. No separate stored SPACE object is required.

The common-origin view retains ordered rays from the root; the attached-origin
view uses their prefix sums. Exact differences recover the original rays.
Both serialize the root location and SPACE orientation. These views need not be
congruent. Graph replay retains carriers, shared child references and every
occurrence; it rejects receipt, root, carrier and relationship mutations.

Native coordinates are exact constructive expressions. Expression identity is
not a complete geometric-equivalence test. Floating display is explicitly lossy
and refuses detected underflow/collapse; it does not supply construction receipts.
No physical camera or sheet-lift law is asserted.

## Explicit bearing candidates

The recursive operation is specified. The exact functional deriving a closed
word's bearing remains unselected; neither candidate has a default:

| Candidate | Bearing supplied to the parent | Boundary |
| --- | --- | --- |
| `root-endpoint-v1` | Direction from the child's root to its endpoint | Requires a proved nonzero endpoint; unsupported nonzero proofs refuse |
| `exit-heading-v1` | Final accumulated heading within the child | Distinct interiors can share this bearing; interiors remain retained |

Comparing these candidates does not introduce an alternative sentence-distance
rule. Native stacks have a nonzero endpoint by strict last-ray dominance. A
compound join need not; native exact zero/unknown checks prevent undefined
endpoint normalization. A bearing is an orientation, not a unique word identity.

## Usage

Install UCNS at `9cc00771e54336d58ee377faeec87a3a33dbd4bf`; the consumer verifies
the exact four source blobs before construction. From the English forge:

```bash
python -m english_gonol.attachment_construction word bull
python -m english_gonol.attachment_construction compound bull shit
python -m english_gonol.attachment_construction sequence bull shit --bearing root-endpoint-v1
python -m pytest -c /dev/null ordinal_tests/test_attachment_construction.py
UCHC_STRUCTURAL_FIELD=/path/to/complete/field python -m pytest -c /dev/null ordinal_tests/test_attachment_corpus.py
python -m english_gonol.attachment_audit /path/to/complete/field --expect experiments/recursive-attachment-v1/corpus-audit.json
```

CLI sequence arguments declare word boundaries; they do not infer sentence
closure. `RecursiveStructuralField.compose(..., relation='sentence')` preserves
the existing structural closure gate. Source queries retain all punctuation,
SPACE events, offsets and word occurrences. The parent geometry's scope is
ordered closed-word placement; it does not invent punctuation function geometry.
Without a bearing, it returns retained word interiors and the narrow partial
`CLOSED_WORD_BEARING_POLICY_REQUIRED`.

`definition()` overlays a typed whole lexical owner, including all components
and provenance, and retains the historical origin separately. A lexical record
ID is never passed as a word ID. This fixes logical ownership; numerical
definition attachment is still open. Historical database bytes and receipts
are not rewritten. Historical word geometry is explicitly qualified under
`historical_structural_geometry` when the new profile returns a word.

## Evidence and remaining scope

The native full outcome gate passes 303 tests, including 24,336 non-SPACE glyph
pairs against an independent cyclotomic oracle, recursive candidate bindings,
graph/view mutation controls and 1,100-level nesting. An independent review
checked attachment closure and the PID-namespace supervisor repair required by
the gate. Consumer checks cover actual native imports, drift/refusal boundaries,
compound replay, shared interiors, and complete-corpus sentence closure.

The complete corpus audit visits every word and definition, checking retained
parts, source succession and typed lexical ownership. Its deterministic stream
digests can be compared across forge and installed consumer. Read the adjacent
experiment evidence for executed counts and exact producer identities.
Acceptance also requires the complete report to match the preserved census via
`--expect`; two equally regressed consumers do not pass. Optimized Python (`-O`
or `PYTHONOPTIMIZE`) is refused because it disables verification assertions.

**hmmm:** select the closed-word bearing functional; numerical definition
attachment; expanded carrier inventory/order; punctuation geometry and sheet
lift; hosted CI, stable publication, released-artifact reconsumption and domain
graduation. Historical ordinal and structural profiles remain explicit replay
interfaces. Rollback selects those versioned profiles without changing receipts.
