# Ordinal radius-halving

At frame radius `R`, zero-based occurrence `i` among `n` has parent-local
radius `R/2**(n-i)`. Appending places the new participant at `R/2` and halves
every earlier parent radius. Each added disc records one level of depth.
The same native UCNS operation accepts closed words. Their local rays and
original source remain recoverable. The default closed-child direction uses
its root-to-endpoint bearing. The caller can explicitly select the retained
`exit-heading-v1` policy. Input text is literal, including spaces and NUL.

A word is an epicycle relative to its glyphs. A sentence is an epicycle
relative to its words. Each scale exposes two vectors from one set of ordered
operands. `resultant` gives the endpoint of the placed ordinal rays.
`additive_resultant` gives the frame radius times the sum of the children's
complete additive vectors. A scalar contributes a unit vector at its own
SPACE-relative bearing. An additive sum of zero retains its complete ordinal
construction and participates in the next addition.

Install the UCHC package with the `halving` extra, or install the wheel and
supply the exact UCNS checkout via `--ucns-source-root`.

```sh
python -m pip install '.[halving]'
uchc-halving bull
uchc-halving --sequence bull bull
```

```python
from fractions import Fraction
from uchc_halving import construct_text, construct_sequence, closed_record, replay_closed
word = construct_text("bull", source="example:word")
assert [ray.radius for ray in word.rays] == [Fraction(1, n) for n in (16, 8, 4, 2)]
phrase = construct_sequence((word, word), source="example:phrase")
copy = replay_closed(closed_record(phrase))
assert copy.participants[0].interior is copy.participants[1].interior
assert "".join(copy.recover()) == "bullbull"
assert copy.additive_resultant == word.additive_resultant.scaled(2)
```

The CLI's `closed.vectors` contains `placement_endpoint` and
`additive_resultant`. Record version 2 replays the graph and checks both
values. Records from UCHC 0.2.0a2 replay with their original graph identity.
At unit frame radius, grouping `AB | C` or `A | BC` gives the same additive
result. Their exact glyph-ray lengths are respectively `(1/4, 1/2) | (1/2)`
and `(1/2) | (1/4, 1/2)`.

The UCNS scalar turn supplies the glyph bearing, measured from SPACE. Its
UTF-8 spelling follows exactly from the retained scalar. Encoding width never
enters the halving calculation. This profile accepts the full Unicode scalar
range, excluding surrogate code points. The previous bit-width corpus belongs
to Stack. Use its recorded producer to replay old artifacts.

The [ordinal decisions](ordinal-decisions-2026-10-27.md) record the original
recurrence. The earlier [Stack constructor](https://github.com/The-Interdependency/stack/tree/ffd6e52eb1a50291cb48e2168d82e9bc236ceef4/research/english-gonol)
and native UCNS DiskStack supply its provenance. To verify: run
`python -m pytest -q tests/test_halving.py` with the pinned UCNS installation.
