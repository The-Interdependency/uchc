# Architecture boundary

## Dependency direction

```text
UCNS geometry --------------------+
                                  |
METAPAT affixiation semantics ----+--> UCHC domain implementations --> consumer applications
                                  |
bounded language/corpus sources --+
```

UCHC is the intended independent implementation home of the construct;
Stack retains authority for domains whose graduation remains incomplete. A consumer visualization, editor,
browser, or Grok application belongs outside this repository.

## Domain families

```text
human/
  english
  spanish        forthcoming

programming/
  python
  typescript     forthcoming
  rust           forthcoming
```

Each domain may have its own admission, ordering, boundary, and composition rules.
Shared structure may be factored only after two implementations demonstrate the same
law. Similarity alone does not create a universal abstraction.

## Geometry boundary

UCHC consumes UCNS geometry. It does not redefine:

- the Public Gonol carrier;
- gonol object identity or UCNS constructors;
- Möbius return geometry;
- unresolved Public Gonol function operations;
- unresolved continuum lift-selection laws.

Carrier position and UCHC axis participation may coexist as distinct roles of one
glyph identity without becoming interchangeable.

## Hilbert-state migration target

The English Hilbert correction is a Stack-forged candidate until UCHC
graduation completes. Candidate `0.1.0` contains an exact extraction of the
runtime and tests. Until the release transition, fixes originate in Stack and
the extraction inventory verifies the UCHC copy.

```text
O_G: admitted glyph axes
  -> ordered tensor construction
O_W: closed word axes
  -> ordered higher-scale tensor construction
O_D(w): word-local definition axes
```

No Cartesian `x/y/z` basis belongs between UCNS geometry and language
construction. The exact ordered glyph-axis tensor that constructs a word remains
recoverable when the closed word participates atomically as its own word axis.

The candidate requires exact construct identity on each axis and an explicit
scalar field (`R` or `C`). Origin-local axes are orthonormal. Cross-origin
and cross-construct vector inner products remain undefined and fail closed.

A future UCHC input-frame bridge may form an ordered tensor of the already
admitted word/glyph axes while preserving occurrence order and multiplicity.
That bridge is not authoritative in this repository until the Stack candidate
passes the remaining release/reconsumption/authority-transition gates.

Candidate O/S/C displacement maps and epicyclic graph construction remain
downstream candidate operators/readouts. Executability does not make their
channel tuples the language-space coordinates.

## Projection boundary

Consumer applications may choose aesthetic projections that are not metrically
congruent. They must preserve whatever identity, incidence, order, attachment, and
provenance their claimed view requires. A renderer cannot add canonical relations
that UCHC does not contain.

## Usage guidance

Treat [`HILBERT_INFERENCE.md`](HILBERT_INFERENCE.md) as the UCHC migration
contract and provenance boundary. The executable candidate is packaged as
`english_gonol.hilbert_inference`; its complete extraction source is Stack
`ca69c60032a079585ccb89d5cc7aba67f637df55`, recorded in the
[package inventory](package-extraction.json). The
[historical work graph](work-graphs/hilbert-inference.json) retains the original
merged producer. The receipt-bound input API and future input-frame bridge
remain distinct from these origin-local Hilbert helpers.

Do not use a renderer, O/S/C candidate map, or external embedding dimension to
manufacture the basis.

## hmmm

- canonical Hilbert scalar field (`R` or `C`);
- cross-origin inner products and geometric angles;
- amplitude and phase assignment;
- learned inference operators and sense selection;
- sentence-axis promotion;
- stable release and published-artifact reconsumption of the extracted Hilbert candidate;
- geometric consequences of declared local definition-axis orthogonality.
