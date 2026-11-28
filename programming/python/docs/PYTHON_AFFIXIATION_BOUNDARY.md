# Python construction boundary

Status: **stack-local implemented candidate**. This document defines
construction and evidence boundaries; it does not promote Python Gonol
Construction to canon.

## Construction contract

Source bytes are decoded using the Python file encoding. Every scalar has a
native UCNS glyph, four UTF-32BE bytes and an exact bearing. Source occurrences
retain order, multiplicity and provenance. The Public Gonol position is an
optional projection. Four controls also construct named relations and physical
line endings retain their original constituents. See the [Python profile](../README.md).

## Verification boundary

CPython `tokenize` and `ast` verify the construction after the source floor
is admitted. Their outcomes are recorded in the manifest as verification
only; no token, AST, code, or compiler object becomes a gonol or substitutes
for source-built participants.

## Artifacts

One compact SQLite construct plus a small manifest:

```text
construct.db   characters, occurrences, control_identities, controls, newlines, source_bytes, meta
manifest.json  schema, source digests, counts, carrier pin, receipt_sha256, hmmm
```

No giant JSON receipt.

## Replay

Schema 3 binds every character, its native representations and receipt, every
occurrence and all control, newline and provenance records. Verification rebuilds
the complete artifact from the retained original source bytes and rejects a
difference even if an altered database carries newly computed outer digests.
Historical profiles replay with their recorded producers.

## Failure boundary

Invalid or unfinished Python remains constructible: tokenizer/AST failures
are recorded as verification flags and never block source construction.

## Geometry boundary

UCNS owns glyph identity, the SPACE-relative bearing and the Public Gonol projection.
Higher-scale Python relations require their own construction evidence.

## Usage guidance

```bash
cd research/python-gonol
python -m pytest -q tests
python -m python_gonol example.py --out-dir construct --ucns-source-root ~/src/ucns
python -m python_gonol --verify construct --ucns-source-root ~/src/ucns
```

## hmmm

Python grammar and runtime equivalence, language profiles after Python 3.12,
and a large-source streaming policy remain open.
