# Binary origin and repeated-sequence construction

This is a new, executable UCHC binary-domain candidate. It does not move the
English or Python implementation authority, complete their migration, or define
new UCNS geometry. Stack/Weave selects source partitions and operating profiles;
UCHC closes the selected raw-byte sequences and their occurrence relations.

## Construction

One raw-byte message owns a source-bearing `ByteOrigin`. Sequential byte
occurrences are native UCNS axes, addressed on demand. Equal values at different
source positions remain different occurrences. The initial message receipt remains
fixed while each later round has its own source-bound axis frame.

`close_sequences` retains the actual byte definitions and every ordered occurrence.
The eighth/whole circle is numbered 0. Each sequence attaches at its first selected
occurrence's native byte axis; circles 1..7 hold ordered occurrences. This
first-occurrence rule is an explicit binary-domain candidate, not universal UCHC
or UCNS canon. All eight circle-space offsets are caller-supplied exact fractions.

Positions use the real `AxisCirclePosition` and `NativeMobiusState` objects from
UCNS commit `905e66964a495d7596a577bb64e4158db9465864`. The producer verifies and
executes the exact source buffers, never a geometry clone or unchecked path.
A full visible turn reverses the native frame; two turns return the complete state.
The two exact source blob identities are declared in `origin.py`.

`wire_occurrences()` produces seven circle streams, sorted by native complete
position within each circle. `recover_sequences()` inverts their native space
displacements, reconstructs byte placement, checks exact coverage and source
identity, and replays the circle ordering. It accepts neither the original message
nor an encoder trace. This is recoverable positional representation, not a
cryptographic private-key lift. Source identities are not authentication.

## Usage

Python standard library only for these operations. Supply the pinned UCNS checkout.

```sh
PYTHONPATH=binary UCNS_ROOT=/checkout/ucns \
  python3 -m unittest discover -s binary/tests -v
```

```python
from fractions import Fraction
from uchc_binary import Geometry, ByteOrigin, close_sequences

geometry = Geometry('/checkout/ucns')
origin = ByteOrigin(b'ABxABy', 'message-1', 0, geometry)
table = close_sequences(origin, (b'AB', b'x', b'y'), (0, 1, 0, 2),
                        (1, 2, 3), (Fraction(0),) * 8)
assert table.restore() == b'ABxABy'
assert origin.byte_axis(3).turn == Fraction(1, 2)
```

The `uchc_binary` package is included in the existing UCHC wheel. The binary workflow
runs the producer tests against both the source package and an installed clean wheel.
It separately checks event identity; PR merge-ref evidence is not exact-head evidence.

## Validation and boundaries

Tests cover all 256 byte values, equal-value occurrence identity, repeated and
residual sequences, exact 360/720 behavior, effective space offsets, seven-circle
recovery, round separation, leading zero bytes, empty sources, malformed partitions,
coordinate gaps/duplicates, and changed-source refusal before execution.

`work-graph.json` pins starting authorities and expressly describes this new producer
as a change from the UCHC baseline. Consumer locks must pin the resulting producer
commit and module blob, not pretend the baseline already contains this module.

No dictionary, corpus, encoder, fixed circle-visitation schedule, secret-key generator,
or asymmetric-security proof is introduced here. The binary module does not import
language tables and makes no language semantics or cross-origin metric claims.

Rollback removes `binary/uchc_binary`, its tests, workflow and package declaration;
consumers must then refuse the missing source, not switch to replacement geometry.
The owning repository license and notices apply unchanged.

## hmmm

The domain attachment rule remains a named candidate. General cross-origin metric
geometry, cryptographic degeneration/private lifting, public release qualification,
and the existing English/Python migration gates are not established by this work.
