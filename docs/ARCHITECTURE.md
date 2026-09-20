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

## Projection boundary

Consumer applications may choose aesthetic projections that are not metrically
congruent. They must preserve whatever identity, incidence, order, attachment, and
provenance their claimed view requires. A renderer cannot add canonical relations
that UCHC does not contain.

## hmmm

Cross-origin geometric angles and the geometric consequences of declared local
definition-axis orthogonality remain unresolved.
