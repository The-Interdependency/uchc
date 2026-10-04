# UCHC — Unit Circle Hyperspace Constructs

UCHC is the implementation repository for **Unit Circle Hyperspace Constructs**.

Applications consume UCHC; applications do not define UCHC.

## Domains

```text
human/
  english/       extracted from Stack; see migration gate evidence
  spanish/       forthcoming

programming/
  python/        extracted from Stack; see migration gate evidence
  typescript/    forthcoming
  rust/          forthcoming
```

The construct is the implementation. UCHC does not separate a nominal specification layer from a hidden implementation that actually defines the construct.

## Authority boundary

- **UCNS** owns gonol objects, constructors, Public Gonol carrier geometry, Möbius geometry, and other UCNS geometry.
- **METAPAT** owns affixiation semantics where consumed.
- **Stack** remains the current forge and implementation owner for the English and Python gonol workspaces until migration is verified.
- **UCHC** is the intended independent implementation/public-contract boundary for the migrated hyperspace constructs.
- Consumer applications, including visualization applications, consume UCHC and may project it aesthetically; they do not create canonical UCHC structure.
- EDCM may measure/evaluate completed constructions. It does not define them.

Repository placement transfers none of UCNS geometry, METAPAT semantics, proof status, measurement validity, or empirical status.

## Extraction source identities

Scaffold baseline:

- Stack: `The-Interdependency/stack@ca190204de25de240662bb438af80c8dc405cea6`
  - English: `research/english-gonol/`
  - Python: `research/python-gonol/`
- UCNS: `The-Interdependency/ucns@1cf10c2df2541a332a77f2ed3feda0c6bef4abcc`
- METAPAT: `The-Interdependency/metapat@e4165b0cac9eca41daef9c2f941881028ca55d48`
- skill-lib: `The-Interdependency/skill-lib@9a04120686ee4e03338eaf14a81073e467aecfe8`

The English source baseline includes the implemented language hyperspace constructor at
`research/english-gonol/english_gonol/hyperspace_construct.py`.

## English baseline

At the pinned Stack baseline, the completed English hyperspace construction reports:

- 118 admitted source-scalar glyph identities;
- 164,864 word axes;
- 185,155 definition axes;
- three distinct origins: glyph `O_G`, word `O_W`, and per-word definition `O_D(w)`;
- lossless promotion and recovery;
- construction-derived origin attachment;
- cross-frame composition through shared word and glyph identities;
- full-corpus receipt `38b51ab5ebcf7d3e95f3b29700a170d1e7b6d3342dd6088171c5c078a08753d2`.

Carrier position and axis participation are distinct roles of a glyph gonol.

## Hilbert inference target

The axis-native Hilbert correction is currently forged in Stack, which remains
the implementation owner until UCHC graduation completes. UCHC records the
migration target without duplicating a second writable implementation.

```text
glyph axes
  -> ordered glyph-axis tensor
  -> closed word
  -> word axis
  -> ordered higher-scale tensor
```

The target basis comes from the already-declared language axes rather than
external Cartesian `x/y/z` coordinates. A word preserves its exact ordered
glyph construction when closure promotes it into its own higher-scale word
axis.

The Stack candidate binds every axis to the exact construct artifact, requires
an explicit scalar field (`R` or `C`), defines only origin-local
orthonormal inner products, and fails closed on cross-origin/cross-construct
products. The exact merged producer is
`The-Interdependency/stack@6504ed963d93836f66fc88e354fe52809a1a3b7a`.
See [the provisional migration contract](docs/HILBERT_INFERENCE.md); these
Hilbert helpers and the future frame bridge are not available in this UCHC package.

The current UCHC O/S/C inference and epicyclic graph paths remain downstream
candidate operators/readouts. Their executable channel tuples do not define
the Hilbert basis.

## Repository layout

- `human/` — human-language UCHC implementations.
- `programming/` — programming-language UCHC implementations.
- `docs/` — authority, migration, and domain-boundary records.
- `schemas/` — machine contracts after their owning implementation requires them.
- `tests/` — cross-domain conformance tests after migration begins.

No shared `core/` gonol geometry is defined here. Shared geometry is consumed from UCNS rather than reimplemented.

## Usage guidance

English and Python implementations have been extracted, but domain graduation is incomplete.
The receipt-bound English input API is a release candidate, not evidence of a
completed neural inference engine. See [inference input usage](docs/INFERENCE_INPUT.md)
and [Hilbert inference target](docs/HILBERT_INFERENCE.md).
Build the candidate with `python -m pip wheel --no-deps . --wheel-dir dist`,
verify its SHA-256, and install that exact wheel without an editable/source-tree path.
The [input work graph](docs/work-graphs/inference-input.json) records the exact
source authorities used for the input extension; the
[Hilbert work graph](docs/work-graphs/hilbert-inference.json) records the exact
authorities for the axis-native state correction.

Migration order:

1. preserve the exact Stack source identity and receipts;
2. move one domain implementation without semantic or geometric redesign;
3. run its existing tests and replay gates in UCHC;
4. compare behavior/receipts against the pinned Stack source;
5. update the former Stack workspace to consume the released UCHC artifact;
6. only then declare that domain graduated.

## Immutable English artifact

- generated construct file: `construct.db` (not tracked in Git; full-corpus CI materializes and verifies it)
- sha256: `af609bbba504f95e349f3c1a30aa42923acc8e48c1e67bb481521dbf7e49162b`
- full-corpus receipt: `38b51ab5ebcf7d3e95f3b29700a170d1e7b6d3342dd6088171c5c078a08753d2`

The Stack-forged Hilbert candidate consumes this same construction without
altering its receipt. UCHC does not copy that new implementation until the
release/reconsumption/authority-transition gates license the migration.

## License

uchc is licensed under the Functional Source License, Version 1.1, ALv2 Future
License (SPDX: `FSL-1.1-ALv2`). The licensor is Erin Spencer. The full terms are
in [`LICENSE`](LICENSE). Under its Grant of Future License, each version converts
to the ALv2 Future License on the second anniversary of the date it is made
available. [`NOTICE`](NOTICE) records that parts of the English Gonol code were
published earlier under other terms in The-Interdependency/edcm, and it credits
the Open English WordNet input. This section is a licensing map, not legal advice.

## hmmm

- canonical Hilbert scalar field (`R` or `C`);
- exact geometry of definition-axis orthogonality;
- cross-origin inner products, angles, and attachment geometry beyond the implemented construction-derived attachment relation;
- amplitude/phase, sense-selection, and learned inference operators;
- sentence-axis promotion relation;
- migration of the Stack-forged Hilbert candidate into UCHC;
- continuum lift-selection law;
- stable release, published-artifact reconsumption, and domain graduation;
- Spanish, TypeScript, and Rust admission/construction profiles.

The implementation preserves these boundaries rather than filling them with invented structure.
