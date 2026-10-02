# UCHC inference input contract

## Purpose and ownership

Turn exact incoming English text into recoverable access to the constructed
language: admitted native glyphs and words, local definition origins, both
definition topologies, exact components, and source evidence. This is an input
contract, not a neural inference operator or a sense-selection algorithm.

The owning language implementation is `human/english/english_gonol/`.
UCNS retains geometry; METAPAT retains its semantics. Stack's current
`research/zfae/README.md` makes PTCNA the eventual neural-construction owner and
a0 the runtime owner. The a0p fixed-width hash/signature path is a comparison,
not authority to choose a 53-dimensional projection here.

## File plan

| File | Purpose and risk | Required verification |
|---|---|---|
| `human/english/english_gonol/inference_input.py` | Read-only, receipt-bound text resolution; source/identity loss is the main risk. | Exact source/occurrence recovery, candidate-definition completeness, snapshot and replay tamper rejection. |
| `human/english/english_gonol/hilbert_inference.py` | Axis-native mathematical state over the verified input; coordinate substitution or loss of tensor order is the main risk. | UCHC axes as basis, origin-local inner product, recursive word promotion, exact occurrence order, fail-closed cross-origin operations. |
| `human/english/tests/test_inference_input.py` | Focused adversarial reader witnesses. | Unknowns, repeated identities, Unicode, full definition records, closed handles and altered receipts. |
| `human/english/tests/test_hilbert_inference.py` | Focused Hilbert-state witnesses. | Basis orthogonality, word order/multiplicity, frame tensor order, explicit scalar field, cross-origin refusal. |
| `tools/verify_inference_corpus.py` | Exhaustive reader acceptance, not a sample or task-quality claim. | Every admitted glyph, word and definition, all ordered components and semantic evidence rows. |
| `pyproject.toml` | Build the existing domain implementations as an immutable wheel. | Clean wheel installation and tests with source directories absent from imports. |
| `docs/INFERENCE_INPUT.md` | Usage, authority and remaining gates. | Commands replay against the same artifact identities. |

## Interface

`EnglishConstruct` verifies a caller-pinned database SHA-256 and recomputes the
existing full-construct logical receipt. It copies the verified bytes into a
private temporary query snapshot, so later source replacement cannot silently
change an open reader's input. Only derived lookup indexes are added to that
private snapshot; the original database is never written. The snapshot is
query-only after initialization and is removed on `close()`/context exit.

One handle amortizes verification and indexing across requests. Budget disk
for the database copy and its two small evidence indexes before opening it.
No network, model calls or prompt persistence occur inside the reader.

`resolve_text` uses the existing construction's exact non-whitespace-run and
individual-whitespace-scalar rule. It does not lowercase, normalize, strip
punctuation, infer multiword phrases or choose a sense. `word(surface)` also
resolves exact admitted multiword surfaces; `iter_words()` covers every word
axis independently of text segmentation.

Each `InferenceFrame` carries source-scoped occurrences and the native producer
objects. Repeated input occurrences share the same native object within the
frame. All definitions of each referenced word remain candidates in their
source order. Frame definition references can be recovered through
`definition(id)` on the same construct; they are not truncated, flattened or
recursively copied into a second corpus. Definition components and semantic
relations retain their original typed identities and provenance.

A frame's receipt binds the complete input dossier and the verified construct
identity. Digests provide integrity, not semantics or authentication. The
Unicode database version is recorded because the existing non-carrier glyph
constructor consumes Unicode names.

Unknown words and scalars preserve their exact spelling, order and spans;
`require_complete()` refuses them. An admitted component with no definitions is
not evidence that its meaning was resolved. Empty input is structurally empty,
not an inference result. No ready flag here authorizes neural inference.

## Hilbert-state bridge

A complete frame can now be lifted into its native mathematical inference
state without introducing an external coordinate system:

```text
exact source occurrences
  -> admitted word / glyph identities
  -> existing UCHC axes
  -> ordered tensor basis state
```

`frame_basis_state(frame, construct)` maps each admitted non-whitespace
occurrence to its existing word axis and each whitespace scalar to its glyph
axis. It preserves occurrence order and multiplicity exactly.

For an admitted word, `word_promotion` exposes the lower-scale ordered
glyph-axis tensor and the word axis into which that closed construction
promotes. Thus the word axis is not a numerical embedding synthesized from the
glyphs; it is the higher-scale axis produced by closure while the glyph
construction remains recoverable.

The bridge chooses no O/S/C channel, semantic sense, weight, amplitude, or
phase. Origin-local vector arithmetic requires an explicit scalar field
(`R` or `C`), because the canonical inference field remains unresolved.
Cross-origin inner products fail closed.

See [`HILBERT_INFERENCE.md`](HILBERT_INFERENCE.md) for the mathematical
contract and failure conditions.

## Usage guidance

Install the exact built wheel (verify its SHA-256 first), then:

```python
from pathlib import Path
from english_gonol.hilbert_inference import frame_basis_state
from english_gonol.inference_input import EnglishConstruct

with EnglishConstruct(
    Path('/data/construct.db'),
    database_sha256='<verified database SHA-256>',
    logical_receipt='<verified full-construct logical receipt>',
) as construct:
    frame = construct.resolve_text('alpha letter alpha.', source_id='request:1')
    frame.require_complete()
    state = frame_basis_state(frame, construct)
    print(state.space_signature)

    for word in frame.words:
        for definition_id in word.definition_ids:
            definition = construct.definition(definition_id)
            print(definition.text, definition.evidence)

    assert construct.replay(frame.to_bytes()) == frame
```

The complete pinned English artifact has logical receipt
`12277b4959c0c72b7af12097b8a77bf91866bbf669e7f4ac07b6a5f1426ebb57`.
Use the actual database byte digest delivered with its verified artifact;
this logical receipt does not substitute for that physical identity.

Run the focused witnesses with:

```bash
python -m pytest -q \
  human/english/tests/test_inference_input.py \
  human/english/tests/test_hilbert_inference.py
```

Exhaustive reader acceptance is
`python tools/verify_inference_corpus.py --database /data/construct.db
--database-sha256 <digest> --logical-receipt <receipt> --output /tmp/input-receipt.json`.
It requires all corpus rows, never a smaller sample.

## Rollout and rollback

Build and clean-install the candidate, run the same bytes in the Stack consumer,
and retain their immutable identity. Release/reconsumption and authority
transition must still follow `docs/MIGRATION.md`; this contract alone does not
graduate UCHC.

The Hilbert layer is additive over the existing immutable construction: it does
not change `construct.db` or the existing full-corpus hyperspace receipt.
Rollback removes `hilbert_inference.py`, its tests, and its documentation; the
verified source construction remains intact.

## hmmm

- canonical scalar field (`R` or `C`);
- cross-origin inner products and angles;
- propagation/learning and readout laws;
- amplitude and phase assignment;
- context-dependent sense selection;
- sentence-axis promotion and later recursive scales;
- broader admission and useful held-out inference.

No coordinate or weight dimension is invented to conceal those boundaries.
