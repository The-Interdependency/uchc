# Recursive Unicode construction

GPT generated; context, prompt Erin Spencer.

The forward English API is `english_gonol.unicode_construction`. It adds
native Unicode glyphs, complete text frames and its own completed sequences.
SPACE, punctuation, newlines, NUL, precomposed and decomposed text remain distinct
without normalization. Glyphs retain 16 b rad, 32-bit big-endian diameters and
their exact UTF-8 anatomy at every depth.

```python
from english_gonol.unicode_construction import (
    construct_text, construct_sequence, resultant, closed_record, replay_closed,
)

root = "/path/to/pinned-ucns"
word = construct_text("Aë e\u0308!\n", ucns_source_root=root)
pair = construct_sequence((word, word), source="example:pair", ucns_source_root=root)
parent = construct_sequence((pair, pair), source="example:parent", ucns_source_root=root)
copy = replay_closed(closed_record(parent, ucns_source_root=root), ucns_source_root=root)
assert copy.recover() == word.text * 4
assert copy.receipt == parent.receipt
assert resultant(parent, ucns_source_root=root) == resultant(word, ucns_source_root=root).scaled(4)
```

Use the exact UCNS commit and four source digests from `authority()` and the
[shared work graph](../../../docs/work-graphs/unicode-recursive-v1.json). The
adapter verifies every source file before executing any bytes. It imports no
ambient UCNS installation and implements no geometry itself.

Each completed child remains the actual retained object. Its exact vector result
enters the next addition, carrying radius and direction together. No unit
normalization or independent parent bearing is imposed. A zero result retains
its complete graph and participates again. Optional exact rotations and a common
scale apply explicit linear transforms while retaining the child objects.
Explicit `bearings` select the historical declared-placement API.

The [extraction record](../experiments/unicode-recursive-v1/extraction.json) binds
the exact Stack source and tests. Stack remains the language forge. The old
attachment adapter also now validates completed sequences by their retained
structure and accepts them recursively under its explicit historical policies.
Stored historical glyph/sequence receipts do not change.

Verification, from the UCHC root:

```sh
PYTHONPATH=human/english python tools/verify_unicode_extraction.py /path/to/stack --ucns-source-root /path/to/ucns
PYTHONPATH=human/english UCHC_UNICODE_UCNS_ROOT=/path/to/ucns python -m pytest -c /dev/null tests/test_unicode_recursive.py tests/test_unicode_verification.py
```

Repeat the extraction verifier with `python -I` in a clean installed environment;
the source and installed JSON results must match. The workflow also tests the
installed wheel outside source paths. Rollback reselects the prior pinned package
and producer; historical extraction records remain archived.

**hmmm:** the general scale-transition law, corpus extraction,
stable release and domain graduation remain separate. Addition needs no independent bearing selector.
