# English ordinal geometry — executable UCNS consumer

**Status:** New UCHC consumer of existing UCNS geometry. The sealed English corpus and Stack's forge authority do not change.

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

The geometry API constructs a raw glyph frame for verified admitted text and separately preserves the ordered internal geometry of each closed word identity. It does **not** assign an invented angular carrier to the higher word frame; that separate geometry remains hmmm. Other operations, such as displacement, retain their explicit refusal.

## Evidence and failure

The new consumer:

- imports the actual UCNS Carrier, Participant, Construction and affixiate objects;
- pins and validates the exact Git blobs of UCNS ordinal_affixiation.py and public_gonol.py;
- rejects missing Public Gonol glyph bearings rather than inventing coordinates;
- refuses unverified/partial English corpus bindings;
- preserves source order, repetition, provenance, closure and immutable corpus receipts.

The hosted workflow uses a pinned actual UCNS checkout, runs independent append-oracle and source-drift tests, and verifies the clean-installed UCHC wheel.

Machine authority graph: [english-ordinal-geometry-v1.json](../../docs/work-graphs/english-ordinal-geometry-v1.json).

## DONE WHEN / PROVEN BY / FAILS IF

**DONE WHEN:** UCHC constructs real UCNS glyph geometry for admitted sequences and exposes it in a corpus-aware consumer.

**PROVEN BY:** word = R/16, R/8, R/4, R/2; repeated glyphs have unchanged angles and different radii; complete recovery and UCNS-native objects; named refusal for missing angle, source drift and unverified corpus; a clean installed wheel passing cross-repository tests.

**FAILS IF:** UCHC synthesizes local bearings/radii, calls undifferentiated potential a gonol, silently admits missing glyphs, falsifies a higher-order frame, or rewrites a sealed corpus.

## hmmm

1. The public 157-glyph carrier does not yet give every Unicode scalar in the broader English corpus a licensed angular bearing. Unsupported glyphs refuse; an explicitly specified expanded public angular carrier is needed for complete coverage.
2. Angular attachment of closed words to a higher carrier and transport between word/definition frames are not selected.
3. This consumer does not by itself complete Stack-to-UCHC graduation, full-corpus geometric census, native Möbius lift, or semantic measurement.
