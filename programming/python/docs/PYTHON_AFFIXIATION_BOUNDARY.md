# Python construction boundary

Status: **stack-local implemented candidate**. This document defines
construction and evidence boundaries; it does not promote Python Gonol
Construction to canon.

## Construction contract

Python source is constructed with the English method:

```text
source bytes
  -> exact decoded source
  -> one shared identity per pinned Public Gonol glyph
  -> ordered occurrence references (address, line, column, provenance)
  -> control constructions: TAB, LF, FF, CR
  -> logical newlines: LF, CR, CR+LF
```

A parent may reference only an already-closed child. Closing a larger gonol
never erases the child's identity, order, multiplicity, source span,
relation, or provenance.

## Carrier boundary

UCNS owns geometry and the exact 157-position Public Gonol carrier. The
builder consumes the pinned carrier (`ucns@62e08ee`) and digest; it never
copies, extends, or reinterprets it. Every pinned glyph has one shared
character identity.

The four control scalars are constructed from the carrier glyphs of their
Unicode names and code points:

```text
CHARACTER TABULATION + U+0009 -> TAB
LINE FEED          + U+000A -> LF
FORM FEED          + U+000C -> FF
CARRIAGE RETURN    + U+000D -> CR
```

Names and code points are constitutive participants, not metadata. TAB
affixiates with enough SPACE gonols to reach the next eight-column stop. CR,
LF, and CR+LF construct logical newlines while preserving their exact source
constituents and remaining source-distinct.

Any other off-carrier source scalar is recorded as hmmm with its exact
address and is never assigned an invented Public Gonol position.

## Verification boundary

CPython `tokenize` and `ast` verify the construction after the source floor
is admitted. Their outcomes are recorded in the manifest as verification
only; no token, AST, code, or compiler object becomes a gonol or substitutes
for source-built participants.

## Artifacts

One compact SQLite construct plus a small manifest:

```text
construct.db   characters, occurrences, control_identities, controls, newlines, meta
manifest.json  schema, source digests, counts, carrier pin, receipt_sha256, hmmm
```

No giant JSON receipt.

## Replay

Replay verifies, at minimum:

1. pinned Public Gonol digest and module digest;
2. exact source bytes and decoded-source digests;
3. contiguous ordered occurrence coverage with exact address, span, line,
   and column;
4. every carrier glyph occurrence references its single shared identity and
   exact pinned position;
5. control constructions match the recomputed TAB/LF/FF/CR rows exactly;
6. logical newlines match the recomputed LF/CR/CRLF rows exactly;
7. off-carrier non-control scalars carry no invented identity or position;
8. the canonical receipt digest matches.

Replay proves this construction is internally reproducible. It does not
establish semantic quality, runtime equivalence, measurement validity, or
canon.

## Failure boundary

Invalid or unfinished Python remains constructible: tokenizer/AST failures
are recorded as verification flags and never block source construction.

## Geometry boundary

UCNS owns geometry. The builder observes only the pinned Public Gonol
positions and records deeper geometric function operations as hmmm.

## Usage guidance

```bash
cd research/python-gonol
python -m pytest -q tests
python -m python_gonol example.py --out-dir construct --ucns-source-root ~/src/ucns
python -m python_gonol --verify construct --ucns-source-root ~/src/ucns
```

## hmmm

- deeper geometric functions of Public Gonol positions remain unresolved;
- admission of arbitrary Unicode source characters remains unresolved and is
  preserved without invention;
- full CPython 3.12 grammar/test-corpus parity replay;
- language profiles after Python 3.12;
- large-source streaming/checkpoint policy.
