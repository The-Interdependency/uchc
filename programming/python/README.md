# Python source construction

Schema `python-gonol.full-construct` version `3.0.0` preserves the exact bytes
and decoded occurrences of a Python 3.12 source file in `construct.db`. Its
`manifest.json` binds the source, native UCNS modules, schema, rows and replay.

Every decoded scalar has one shared character identity equal to its Unicode
scalar value. The native UCNS glyph supplies four UTF-32BE bytes, its UTF-8
spelling, its exact SPACE-relative bearing and its glyph receipt. The
157-position Public Gonol supplies an optional position. The character table
includes that inventory and any additional scalars used by the file. Each
occurrence references its character and keeps its ordinal, address, line and
column. Repeated glyphs at different source locations share their identity.

For example, `ë` records `00 00 00 EB` and `🐍` records `00 01 F4 0D`.
A decomposed `e` followed by U+0308 retains two occurrences. A Latin-1 source
can store `ë` as one byte while its glyph retains those same four UTF-32BE bytes.
The original input encoding and byte-order marker are recoverable.

TAB, LF, FF and CR carry their glyph identities and their control constructions.
Control names and code points are ordered glyph participants. Tabs expand to
the next eight-column stop. CR, LF and CRLF retain their distinct source
constituents. The tokenizer and syntax-tree results are recognition witnesses.

## Construct and verify

Use Python 3.12+ and the UCNS checkout pinned in [BASE.json](BASE.json).
For an installed UCHC wheel, run from any directory. In Stack, run from
`research/python-gonol/`.

```sh
python -m python_gonol source.py --out-dir construct --ucns-source-root /path/to/ucns
python -m python_gonol --verify construct --ucns-source-root /path/to/ucns
```

`affixiate_python_bytes` accepts original bytes. `affixiate_python_source`
accepts decoded text. `verify_construct` rebuilds the artifact from retained
bytes and verifies its schema, rows, glyph identities and receipt. Non-scalar
surrogates and failed source decoding are rejected.

To migrate schema 1 or 2, build into a fresh directory from the original file.
Schema 2 also retains those bytes in `source_bytes.data` at `id=1`. Keep the
historical receipt with its producer. The new schema produces a new receipt.

**hmmm** — Constructing Python assignment, scope and runtime relations remains
a separate language-construction problem.
