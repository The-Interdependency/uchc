# UCHC — Unit Circle Hyperspace Constructs

UCHC is the implementation repository for **Unit Circle Hyperspace Constructs**.

Applications consume UCHC; applications do not define UCHC.

## Domains

```text
human/
  english/       extracted from Stack; migration gates 1-5 passed
  spanish/       forthcoming

programming/
  python/        extracted from Stack; migration gates 1-5 passed
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

## Current source identities

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

## Repository layout

- `human/` — human-language UCHC implementations.
- `programming/` — programming-language UCHC implementations.
- `docs/` — authority, migration, and domain-boundary records.
- `schemas/` — machine contracts after their owning implementation requires them.
- `tests/` — cross-domain conformance tests after migration begins.

No shared `core/` gonol geometry is defined here. Shared geometry is consumed from UCNS rather than reimplemented.

## Usage guidance

This scaffold is **not yet a released runtime dependency**. Until implementation migration is complete, consumers must not treat the empty domain directories as equivalent to the live Stack implementations.

Migration order:

1. preserve the exact Stack source identity and receipts;
2. move one domain implementation without semantic or geometric redesign;
3. run its existing tests and replay gates in UCHC;
4. compare behavior/receipts against the pinned Stack source;
5. update the former Stack workspace to consume the released UCHC artifact;
6. only then declare that domain graduated.

## Immutable English artifact

- construct file: `human/english/experiments/full-construct-v2-local/construct.db`
- sha256: `af609bbba504f95e349f3c1a30aa42923acc8e48c1e67bb481521dbf7e49162b`
- full-corpus receipt: `38b51ab5ebcf7d3e95f3b29700a170d1e7b6d3342dd6088171c5c078a08753d2`

## hmmm

- exact geometry of definition-axis orthogonality;
- cross-origin angles and attachment geometry beyond the implemented construction-derived attachment relation;
- continuum lift-selection law;
- release/distribution format for UCHC;
- Spanish, TypeScript, and Rust admission/construction profiles.

The scaffold preserves these boundaries rather than filling them with invented structure.
