# Architecture boundary

## Dependency direction

```text
UCNS geometry --------------------+
                                  |
METAPAT affixiation semantics ----+--> UCHC domain implementations --> consumer applications
                                  |
bounded language/corpus sources --+
```

UCHC is the implementation of the construct. A consumer visualization, editor,
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

## Hilbert-state boundary

The English inference state uses the axes already present in the UCHC
construction as mathematical basis directions.

```text
O_G: admitted glyph axes
  -> ordered tensor construction
O_W: closed word axes
  -> ordered higher-scale tensor construction
O_D(w): word-local definition axes
```

No Cartesian `x/y` coordinate basis is inserted between UCNS geometry and UCHC
language construction. The exact ordered glyph-axis tensor that constructs a
word remains recoverable after that word closes and participates atomically as
its own word axis.

Each origin-local admitted basis defines a finite-dimensional Hilbert space once
its scalar field is explicitly chosen as `R` or `C`; finite dimension supplies
completeness. The current construction does not canonize which scalar field
future inference amplitudes use, so implementations must name it rather than
defaulting silently.

A complete input frame inhabits the tensor product of the origin-local spaces
selected by its occurrence stream. Tensor factors preserve order and
multiplicity. This supplies a Hilbert state without asserting cross-origin
angles: an inner product between `O_G`, `O_W`, or distinct `O_D(w)` spaces is
undefined until separately licensed.

Candidate O/S/C displacement maps and epicyclic graph construction operate
downstream of this state boundary. Executability does not make their channel
triples the language-space coordinates.

## Projection boundary

Consumer applications may choose aesthetic projections that are not metrically
congruent. They must preserve whatever identity, incidence, order, attachment, and
provenance their claimed view requires. A renderer cannot add canonical relations
that UCHC does not contain.

## Usage guidance

Use `english_gonol.hilbert_inference.frame_basis_state` to construct the
axis-native tensor state of a complete `InferenceFrame`. Use
`word_promotion`/`definition_promotion` when auditing how a lower-scale ordered
construction becomes a higher-scale axis. Do not use a renderer, an O/S/C
candidate map, or an external embedding dimension to manufacture the basis.

## hmmm

- canonical Hilbert scalar field (`R` or `C`);
- cross-origin inner products and geometric angles;
- amplitude and phase assignment;
- learned inference operators and sense selection;
- sentence-axis promotion;
- geometric consequences of declared local definition-axis orthogonality.
