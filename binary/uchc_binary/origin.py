# === MODULE_BUILD ===
# id: uchc_binary_origin_affixiation
#   module_name: uchc_binary.origin
#   module_kind: engine
#   summary: raw-byte origins and closed repeated-sequence participation using source-pinned native UCNS axis and Mobius constructors
#   owner: Erin Spencer
#   public_surface: Geometry, ByteOrigin, Occurrence, ClosedSequence, SequenceTable, close_sequences, recover_sequences
#   internal_surface: exact source loader and canonical construction receipts
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: binary/tests/test_origin.py
#   rollout: explicit binary-domain construction; no English or Python migration
#   rollback: remove binary package and its package/workflow declarations
#   requires: ucns_axis_circle_position_candidate, ucns_native_mobius_geometry
#   unresolved: cryptographic public/private lift and cross-origin metric geometry are not supplied
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: binary_origin_byte_axes
#   given: exact raw bytes at a message-origin and round
#   then: every byte occurrence is addressable by its native UCNS axis without collapsing equal values
# id: binary_sequence_closure
#   given: unique byte-sequence definitions and an ordered partition of a source
#   then: closure retains sequence values, byte order, multiplicity, and both source and occurrence-circle attachments
# id: binary_native_geometry
#   given: the exact declared UCNS source modules and supplied space relations
#   then: native axis and Mobius objects perform all geometric construction; 360 and 720 returns remain distinct
# id: binary_coordinate_recovery
#   given: definitions, seven ordered circle streams and their native complete positions
#   then: inverse native displacement recovers exact source placement without an original-message copy
# id: binary_source_refusal
#   given: missing or changed UCNS source or invalid occurrence/partition inputs
#   then: refuse instead of substituting geometry or silently repairing data
# === END CONTRACTS ===
"""Binary-domain origin and sequence closure, not a cipher or language model.

Usage: geometry = Geometry('/checkout/ucns')
       origin = ByteOrigin(b'ABxABy', 'message-1', 0, geometry)
       table = close_sequences(origin, (b'AB', b'x', b'y'), (0,1,0,2),
                               (1,2,3), (Fraction(0),) * 8)
       assert table.restore() == b'ABxABy'

The caller owns segmentation and circle/space selection. This producer owns raw
byte participation and closure; UCNS owns every geometric object. Source receipts
identify constructions; they are not substitutes for the retained bytes, secret
keys, authentication, or mathematical proof. Byte axes are determinable on demand.
The eighth/whole circle uses index 0 in this API; occurrence circles are 1..7.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from hashlib import sha1, sha256
from pathlib import Path
from types import ModuleType
import json
import re
import sys

SCHEMA = 'uchc.binary-sequence-origin'
VERSION = '0.1.0'
UCNS_COMMIT = '905e66964a495d7596a577bb64e4158db9465864'
UCNS_BLOBS = {
    'src/ucns/axis_circle.py': '768777c8eca6e65537fdbab2003835d6f4f40569',
    'src/ucns/direct_mobius.py': '14a4cee36b5bbfa72cf3c03703c427abdac7f33d',
}


class BinaryError(ValueError):
    """Invalid native source, byte-origin, or sequence closure."""


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def _digest(obj) -> str:
    return sha256(canonical(obj)).hexdigest()


def _natural(value, name: str) -> int:
    if type(value) is not int or value < 0:
        raise BinaryError(f'{name} must be a nonnegative integer')
    return value


def _sha(value: str) -> str:
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}', value) is None:
        raise BinaryError('exact lowercase SHA-256 identity required')
    return value


def _load_exact(path: Path, expected: str) -> ModuleType:
    try:
        with path.open('rb') as source:
            data = source.read(65537)
    except OSError as exc:
        raise BinaryError(f'UCNS source unavailable: {path}') from exc
    actual = sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if len(data) > 65536 or actual != expected:
        raise BinaryError(f'UCNS source identity mismatch: {path}')
    name = '_uchc_ucns_' + expected
    # Execute the exact checked buffer, not a second disk read (no check/use race).
    # Unique module names retain native class identity across Geometry instances.
    if name not in sys.modules:
        module = ModuleType(name)
        module.__file__ = str(path)
        sys.modules[name] = module
        try:
            exec(compile(data, str(path), 'exec'), module.__dict__)
        except BaseException:
            sys.modules.pop(name, None)
            raise
    return sys.modules[name]


class Geometry:
    """Read the two exact UCNS modules; no network, package shadow, or fallback."""
    def __init__(self, ucns_root: str | Path):
        root = Path(ucns_root)
        self.axis_module = _load_exact(root/'src/ucns/axis_circle.py',
                                      UCNS_BLOBS['src/ucns/axis_circle.py'])
        self.mobius_module = _load_exact(root/'src/ucns/direct_mobius.py',
                                        UCNS_BLOBS['src/ucns/direct_mobius.py'])

    def axis(self, origin_sha256: str, count: int, ordinal: int):
        return self.axis_module.build_axis_circle_position(
            origin_sha256=origin_sha256, axis_count=count, axis_ordinal=ordinal)

    def placed(self, axis, space: Fraction):
        if type(space) is not Fraction:
            raise BinaryError('space relationship must be an exact Fraction')
        return self.mobius_module.native_mobius_state(axis.turn - space)

    def recover_axis(self, origin: str, count: int, position: Fraction, space: Fraction):
        """Invert the native frame displacement and recover its exact source axis."""
        if type(position) is not Fraction or not 0 <= position < 2:
            raise BinaryError('canonical complete position in [0,2) required')
        if type(space) is not Fraction:
            raise BinaryError('exact Fraction space relationship required')
        state = self.mobius_module.native_mobius_state(position).advance(space)
        ordinal = state.phase_turns * count
        if state.frame.sign != 1 or ordinal.denominator != 1:
            raise BinaryError('position does not lift to a source byte axis')
        return self.axis(origin, count, ordinal.numerator)

    def lift(self, state) -> Fraction:
        """Serialize the native complete frame in [0,2), not just visible phase."""
        return state.phase_turns + (1 if state.frame.sign < 0 else 0)


@dataclass(frozen=True)
class ByteOrigin:
    source: bytes = field(repr=False)
    scope: str
    round_id: int
    geometry: Geometry = field(repr=False, compare=False)
    message_origin: str | None = None

    def __post_init__(self):
        if type(self.source) is not bytes:
            raise BinaryError('exact raw bytes required')
        if type(self.scope) is not str or not self.scope or len(self.scope.encode('utf-8')) > 1024:
            raise BinaryError('nonempty message scope of at most 1024 UTF-8 bytes required')
        _natural(self.round_id, 'round')
        if type(self.geometry) is not Geometry:
            raise BinaryError('native Geometry required')
        source_digest = sha256(self.source).hexdigest()
        if self.round_id == 0:
            root = _digest({'schema': SCHEMA, 'version': VERSION, 'scope': self.scope,
                            'byte_length': len(self.source), 'source_sha256': source_digest})
            if self.message_origin is not None and self.message_origin != root:
                raise BinaryError('initial message-origin does not identify the source')
            object.__setattr__(self, 'message_origin', root)
        else:
            _sha(self.message_origin)
        # Memoize the source digest once. Axis queries must not re-hash the source.
        identity = _digest({'schema': SCHEMA, 'version': VERSION, 'scope': self.scope,
                            'message_origin': self.message_origin, 'round': self.round_id,
                            'byte_length': len(self.source), 'source_sha256': source_digest})
        object.__setattr__(self, '_identity', identity)

    @property
    def identity(self) -> str:
        return self._identity

    def byte_axis(self, offset: int):
        _natural(offset, 'byte offset')
        if offset >= len(self.source):
            raise BinaryError('byte offset outside this round')
        return self.geometry.axis(self.identity, len(self.source), offset)


@dataclass(frozen=True)
class Occurrence:
    source_offset: int
    circle: int
    ordinal: int
    source_axis: object
    circle_axis: object
    state: object
    source_state: object


@dataclass(frozen=True)
class ClosedSequence:
    data: bytes = field(repr=False)
    attachment_axis: object
    state: object
    occurrences: tuple[Occurrence, ...]

    @property
    def repeated(self) -> bool:
        return len(self.data) >= 2 and len(self.occurrences) >= 2


@dataclass(frozen=True)
class SequenceTable:
    origin: ByteOrigin
    definitions: tuple[ClosedSequence, ...]
    order: tuple[int, ...]

    def restore(self) -> bytes:
        """Read definitions and occurrence order, not origin.source."""
        return b''.join(self.definitions[i].data for i in self.order)

    def wire_occurrences(self) -> tuple[tuple[int, Occurrence], ...]:
        """Seven circle streams, each ordered by its native complete local position."""
        items = [(i, o) for i, d in enumerate(self.definitions) for o in d.occurrences]
        return tuple(sorted(items, key=lambda item: (
            item[1].circle, self.origin.geometry.lift(item[1].state))))

    def receipt(self) -> dict:
        return {'schema': SCHEMA, 'version': VERSION, 'origin': self.origin.identity,
                'message_origin': self.origin.message_origin, 'round': self.origin.round_id,
                'definitions': [
                    {'length': len(d.data), 'source_sha256': sha256(d.data).hexdigest(),
                     'attachment': d.attachment_axis.as_dict(),
                     'complete_turn': str(self.origin.geometry.lift(d.state)),
                     'occurrences': [
                         {'source_offset': o.source_offset, 'circle': o.circle,
                          'ordinal': o.ordinal, 'source_axis': o.source_axis.as_dict(),
                          'circle_axis': o.circle_axis.as_dict(),
                          'complete_turn': str(self.origin.geometry.lift(o.state)),
                          'source_turn': str(self.origin.geometry.lift(o.source_state))}
                         for o in d.occurrences]}
                    for d in self.definitions], 'order': list(self.order)}


def close_sequences(origin: ByteOrigin, blocks: tuple[bytes, ...],
                    order: tuple[int, ...], circles: tuple[int, ...],
                    spaces: tuple[Fraction, ...]) -> SequenceTable:
    """Close an exact ordered partition using native whole/occurrence attachments.

    The caller supplies selection and assignments. The explicit binary-domain
    attachment rule uses the first selected occurrence's native byte axis for a
    sequence's whole-circle attachment; occurrence circles retain source offsets
    and ordered native local axes. No cross-origin angle or inner product is claimed.
    """
    if type(origin) is not ByteOrigin:
        raise BinaryError('ByteOrigin required')
    if any(type(v) is not tuple for v in (blocks, order, circles, spaces)):
        raise BinaryError('immutable partition inputs required')
    if len(circles) != len(blocks) or len(spaces) != 8:
        raise BinaryError('one circle per definition and exactly eight space relationships required')
    if any(type(s) is not Fraction for s in spaces):
        raise BinaryError('exact Fraction space relationships required')
    if any(type(b) is not bytes or not b for b in blocks) or len(set(blocks)) != len(blocks):
        raise BinaryError('definitions must be unique nonempty byte sequences')
    if any(type(c) is not int or not 1 <= c <= 7 for c in circles):
        raise BinaryError('occurrence circle must be 1..7')
    if len(blocks) > len(origin.source) or len(order) > len(origin.source):
        raise BinaryError('partition cardinality exceeds source byte count')
    slots = [[] for _ in range(8)]
    uses = [[] for _ in blocks]
    offset = 0
    for index in order:
        if type(index) is not int or not 0 <= index < len(blocks):
            raise BinaryError('undefined sequence reference')
        block = blocks[index]
        if offset + len(block) > len(origin.source) or origin.source[offset:offset+len(block)] != block:
            raise BinaryError('partition does not reconstruct the declared source')
        circle = circles[index]
        ordinal = len(slots[circle])
        slots[circle].append((offset, len(block)))
        uses[index].append((offset, circle, ordinal))
        offset += len(block)
    if offset != len(origin.source) or any(not group for group in uses):
        raise BinaryError('partition omits source bytes or contains unused definitions')
    circle_origins = [_digest({'origin': origin.identity, 'circle': i, 'slots': slots[i]})
                      for i in range(8)]
    definitions = []
    for index, block in enumerate(blocks):
        attachment = origin.byte_axis(uses[index][0][0])
        occurrences = []
        for start, circle, ordinal in uses[index]:
            source_axis = origin.byte_axis(start)
            local_axis = origin.geometry.axis(circle_origins[circle], len(slots[circle]), ordinal)
            occurrences.append(Occurrence(start, circle, ordinal, source_axis, local_axis,
                                          origin.geometry.placed(local_axis, spaces[circle]),
                                          origin.geometry.placed(source_axis, spaces[circle])))
        definitions.append(ClosedSequence(block, attachment,
                           origin.geometry.placed(attachment, spaces[0]), tuple(occurrences)))
    return SequenceTable(origin, tuple(definitions), order)


def recover_sequences(geometry: Geometry, *, scope: str, message_origin: str,
                      round_id: int, origin_identity: str, byte_length: int,
                      blocks: tuple[bytes, ...], circles: tuple[int, ...],
                      spaces: tuple[Fraction, ...], counts: tuple[int, ...],
                      wire_order: tuple[int, ...], source_turns: tuple[Fraction, ...],
                      max_bytes: int = 1048576) -> SequenceTable:
    """Recover source placement from seven native circle streams, then close again.

    No original message, plaintext occurrence list, or encoder trace is accepted.
    The transmitted complete positions and supplied circle-space relationships
    determine source axes. This is a reversible positional representation, not a
    secret-key advantage or authenticated decryption.
    """
    if type(geometry) is not Geometry:
        raise BinaryError('native Geometry required')
    _sha(origin_identity)
    _sha(message_origin)
    _natural(byte_length, 'source byte length')
    if type(max_bytes) is not int or max_bytes < 1 or byte_length > max_bytes:
        raise BinaryError('source byte length exceeds reconstruction budget')
    if any(type(v) is not tuple for v in (blocks, circles, spaces, counts, wire_order, source_turns)):
        raise BinaryError('immutable reconstruction records required')
    if len(circles) != len(blocks) or len(spaces) != 8 or len(counts) != 7:
        raise BinaryError('invalid circle reconstruction cardinality')
    if any(type(b) is not bytes or not b for b in blocks):
        raise BinaryError('nonempty byte definitions required')
    if any(type(c) is not int or not 1 <= c <= 7 for c in circles):
        raise BinaryError('occurrence circle must be 1..7')
    if any(type(s) is not Fraction for s in spaces):
        raise BinaryError('exact space relationships required')
    if any(type(n) is not int or n < 0 for n in counts):
        raise BinaryError('nonnegative circle occurrence counts required')
    if sum(counts) != len(wire_order) or len(source_turns) != len(wire_order):
        raise BinaryError('circle counts and coordinate records disagree')
    if len(wire_order) > byte_length or len(blocks) > byte_length:
        raise BinaryError('reconstruction cardinality exceeds byte length')
    positions, cursor, total = [], 0, 0
    for circle, count in enumerate(counts, 1):
        for _ in range(count):
            index, turn = wire_order[cursor], source_turns[cursor]
            if type(index) is not int or not 0 <= index < len(blocks) or circles[index] != circle:
                raise BinaryError('reference is not on its declared occurrence circle')
            axis = geometry.recover_axis(origin_identity, byte_length, turn, spaces[circle])
            positions.append((axis.axis_ordinal, index))
            total += len(blocks[index])
            if total > byte_length:
                raise BinaryError('definitions exceed reconstructed byte length')
            cursor += 1
    positions.sort()
    offset, pieces, order = 0, [], []
    for start, index in positions:
        if start != offset:
            raise BinaryError('source positions overlap or leave a gap')
        pieces.append(blocks[index])
        order.append(index)
        offset += len(blocks[index])
    if offset != byte_length:
        raise BinaryError('source positions do not cover the declared stream')
    origin = ByteOrigin(b''.join(pieces), scope, round_id, geometry, message_origin)
    if origin.identity != origin_identity:
        raise BinaryError('reconstructed origin identity differs')
    table = close_sequences(origin, blocks, tuple(order), circles, spaces)
    replay = table.wire_occurrences()
    if tuple(i for i, _ in replay) != wire_order or tuple(geometry.lift(o.source_state) for _, o in replay) != source_turns:
        raise BinaryError('circle streams do not replay in canonical geometric order')
    return table


__all__ = ['SCHEMA', 'VERSION', 'UCNS_COMMIT', 'UCNS_BLOBS', 'BinaryError',
           'Geometry', 'ByteOrigin', 'Occurrence', 'ClosedSequence',
           'SequenceTable', 'close_sequences', 'recover_sequences']
