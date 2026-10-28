# English ordinal geometry — executable UCNS consumer

**Status:** Extracted Stack ordinal candidate consuming existing UCNS geometry.
Stack owns the candidate source and tests until domain graduation. UCHC verifies
their exact extraction before building its candidate wheel. The sealed English
corpus and UCNS geometry authority do not change.

## Construction

Hyperspace is undifferentiated equidistant potential, **not a gonol**. Instantiating glyphs constructs a gonol. The Public Gonol supplies their angular bearings relative to SPACE. UCNS ordinal affixiation supplies their instance radii and exact closure.

For glyph instance i in an n-glyph sequence, with zero-based i:

    radius(i) = R / (2 ** (n - i))

Appending a glyph places it at R/2 and halves every earlier glyph's radius. Repeating a glyph repeats its public angle but not its occurrence radius. UCNS owns the formula, the carrier, the construction objects and receipts; UCHC calls those objects rather than implementing parallel geometry.

For 'word', the final positions are w=R/16, o=R/8, r=R/4, d=R/2, with the four prefixes 'w', 'wo', 'wor', 'word'.

The selected UCNS ordinal Carrier uses the exact 157-position Public Gonol ordering. Its normalized-turn projection is the new ordinal-affixiation operator's angular choice, **not** a retroactive reinterpretation of old Public Gonol artifacts.

## Executable UCHC

Install exact UCNS producer and UCHC, then run:

    python -m pip install 'git+https://github.com/The-Interdependency/ucns.git@ed0b0760f05cd975a7a811f8abeb70a11d09f00b'
    python -m pip install .
    python -m english_gonol.ordinal_construction word

This prints the real UCNS placements, exact rational turns, symbolic halving exponents, source and producer identities, recovered glyphs, and a replay receipt.

Python usage:

    from english_gonol.ordinal_construction import construct_glyph_gonol, geometry_record
    gonol = construct_glyph_gonol("word")
    assert [gonol.placement(i).exponent for i in range(4)] == [4, 3, 2, 1]
    assert gonol.recover() == tuple("word")
    evidence = geometry_record(gonol)

To consume a complete **verified** structural English corpus:

    from english_gonol.ordinal_construction import OrdinalStructuralField
    with OrdinalStructuralField("/path/to/verified/structural-corpus") as field:
        word = field.word("word")
        query = field.construct("word")
        geometry = field.geometry(query, operation="ordinal-affixiation")
        composition = field.compose(query, relation="ordered-text")

The new OrdinalStructuralField is the geometry-enabled API. The historical StructuralField remains available for byte-identical verification of its immutable artifacts. The new consumer does not rewrite historical database rows or receipts.

The geometry API constructs a raw glyph frame when the admitted text has no literal SPACE seam and separately preserves the ordered internal geometry of each closed word identity. The Public Gonol's fixed SPACE position is an origin/seam, not a glyph inserted at nonzero radius. Text crossing a literal SPACE returns **partial** geometry with its word interiors and word-site events preserved, while the cross-word frame remains hmmm. It does **not** invent an angular carrier for the higher word frame. Other operations, such as displacement, retain their explicit refusal.

## Evidence and failure

The new consumer:

- imports the actual UCNS Carrier, Participant, Construction and affixiate objects;
- pins and validates the exact Git blobs of UCNS ordinal_affixiation.py and public_gonol.py;
- rejects missing Public Gonol glyph bearings rather than inventing coordinates;
- refuses unverified/partial English corpus bindings;
- preserves source order, repetition, provenance, closure and immutable corpus receipts.

The hosted workflow uses a pinned actual UCNS checkout, runs independent append-oracle and source-drift tests, and verifies the clean-installed UCHC wheel.

Machine authority graph: [english-ordinal-geometry-v1.json](../../../docs/work-graphs/english-ordinal-geometry-v1.json).

The [extraction receipt](../experiments/ordinal-geometry-v1/extraction.json)
pins the Stack source commit, source/test paths and SHA-256 values. Make candidate
implementation changes in Stack first, then extract and verify the exact bytes
here. This is candidate equivalence, not completed release or graduation.

Each returned word and each detached `word_interiors` entry carries its UCNS
`geometry_authority`, including partial SPACE-seam results. The CI evidence
separately records the tested UCHC commit, PR head, work-graph digest, Stack
extraction identity, construction receipt and built wheel hash.

## Ratified forward requirements

The [operator decisions, clarified 2026-10-28](https://github.com/The-Interdependency/stack/blob/147583a6f23fdc48d5ba59e3baa1d984309c20fb/research/english-gonol/docs/ordinal-decisions-2026-10-27.md)
select construction-derived parent bearing through SPACE, definition ownership
by the whole closed lexical construction, and permission to rebase existing
glyph bearings in a new carrier version with new receipts.

The clarified attachment and storage requirements are also selected:

- Word origins sit at their declared attachments. In `bull + shit`, the second
  `l` occurrence supplies the incoming SPACE attachment while the whole lexical
  construction retains definition ownership.
- The preceding placed letter's direction becomes the next frame's SPACE
  direction. Glyph angles remain relative to their own local SPACE; their
  parent-frame headings can differ even for repeated glyphs.
- Every glyph begins as SPACE. Its original SPACE storage remains together
  with its glyph, origin and angular reference; glyph assignment must not
  discard or replace that support.
- Compound joining preserves component-local radii. Glyph appending remains
  the distinct ordinal-halving operation.

Retained SPACE is a geometric/storage role, not an extra literal U+0020 text
occurrence. The source extraction pinned above remains the tested
implementation. It does not yet implement retained per-glyph SPACE storage,
inherited local-frame direction or origin-at-attachment transport. A word-level
`origin='SPACE'` label does not establish those behaviors.

The earlier shared-origin angular drawing is a projected view, not the complete
attachment construction. Common-origin and individual-origin views require a
recoverable correspondence preserving occurrences, frame relations and SPACE
supports. Sentence joining by distance, angle or both remains a comparison of
alternatives; no sentence operator has been substituted into this runtime.

## DONE WHEN / PROVEN BY / FAILS IF

These acceptance criteria describe the pinned executable extraction above;
they do not mark the newer forward attachment/storage requirements complete.

**DONE WHEN:** UCHC constructs real UCNS glyph geometry for admitted sequences and exposes it in a corpus-aware consumer.

**PROVEN BY:** word = R/16, R/8, R/4, R/2; repeated glyphs have unchanged angles and different radii; complete recovery and UCNS-native objects; named refusal for missing angle, source drift and unverified corpus; a clean installed wheel passing cross-repository tests.

**FAILS IF:** UCHC synthesizes local bearings/radii, calls undifferentiated potential a gonol, silently admits missing glyphs, falsifies a higher-order frame, or rewrites a sealed corpus.

## hmmm

1. The expanded carrier still needs an exact inventory/order and implementation. Rebasing in a new version is authorized; unsupported glyphs continue to refuse in the current pinned implementation.
2. Native retained-SPACE storage, inherited SPACE direction, origin-at-attachment transport and both-view recovery still need implementation and verification. The requirements are selected; sentence distance/angle operators remain candidates.
3. Whole-lexical definition ownership is ratified; its typed-origin implementation and complete-corpus replay remain pending.
4. Stable release, released-artifact reconsumption and Stack-to-UCHC graduation remain incomplete. Native Möbius lift, sheet-state transport and 360°/720° return tests are outside this English ordinal construction's scope.
