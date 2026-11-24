# ratios: loc_comments=132:22 imports_exports=8:8 calls_definitions=60:11
"""UCHC ordinal disc placement. Run `uchc-halving bull` or import construct_text.

Each scalar disc stack carries its ordinal rays and its exact recursive
additive resultant. Completed words retain their interiors.
"""
# === CONTRACTS ===
# id: uchc_recursive_halving
#   given: an ordered nonempty sequence of scalar or closed participants and exact frame radius R
#   then: zero-based occurrence i has radius R/2**(n-i), with replayable order, source and interiors
# id: uchc_recursive_additive_result
#   given: a scalar word or a sequence of completed children
#   then: the same object carries a placed endpoint and an additive resultant, both verified on replay
# === END CONTRACTS ===
from functools import lru_cache
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, distribution
import json
from pathlib import Path
import sys
from threading import Lock
from types import ModuleType

PROFILE = 'uchc.ordinal-halving/1'
_V1_UCNS_COMMIT = 'b9685af7f32dcd0f60adff6ae0ed3b25b6fed877'
_V1_NATIVE_SOURCES = {
    'ordinal_affixiation': '35604a2d2226f97ff865ba26e03a0fe99b5062ba7e6e8645051cfcc096a0558d',
    'scalar_bearing': '7d7ff1e1ddbd4997cdbee4f5f17a7c6fa4b8f3d55e288c97f700f610f32be7ac',
    'attachment_stack': '92b8cbf1510befe2a61c79e7217fecf15b6b257c46f1977b4e970c5c1e67095e',
    'attachment_codec': 'dc7dc62fda8ba087db1cddf4d2fb72147ec9ccadd694b48fc83d3f25471b9e04',
}
UCNS_COMMIT = '1edfa593ae9d8c9ad394b5462638bcc717f99fbd'
NATIVE_SOURCES = {
    **_V1_NATIVE_SOURCES,
    'attachment_stack': 'eed769f1f21c9a2ff469146f494fd76edabc29ea75f389b95a492b738505698a',
}
_NATIVE_LOAD_LOCK = Lock()


@lru_cache(maxsize=1)
def _load_native(sources: tuple) -> ModuleType:
    # All closure bytes have already been verified; no ambient ucns imports.
    name = "_uchc_halving_native_" + sha256(b''.join(data for _, data in sources)).hexdigest()
    package = ModuleType(name)
    package.__path__ = []
    sys.modules[name] = package
    try:
        for local_name, source in sources:
            full_name = name + '.' + local_name
            module = ModuleType(full_name)
            module.__file__ = 'src/ucns/' + local_name + '.py'
            module.__package__ = name
            sys.modules[full_name] = module
            exec(compile(source, module.__file__, "exec"), module.__dict__)
            setattr(package, local_name, module)
    except BaseException:
        for key in tuple(sys.modules):
            if key == name or key.startswith(name + '.'):
                sys.modules.pop(key, None)
        raise
    return package


def _native(ucns_source_root):
    if ucns_source_root is None:
        try:
            directory = Path(distribution('ucns').locate_file('ucns'))
        except PackageNotFoundError as exc:
            raise ValueError('Install uchc[halving] or pass ucns_source_root') from exc
    else:
        directory = Path(ucns_source_root) / 'src/ucns'
    sources = []
    for name, expected in NATIVE_SOURCES.items():
        try:
            source = (directory / (name + '.py')).read_bytes()
        except OSError as exc:
            raise ValueError('UCNS_UNICODE_PRODUCER_REQUIRED') from exc
        if sha256(source).hexdigest() != expected:
            raise ValueError("UCNS_UNICODE_PRODUCER_DRIFT")
        sources.append((name, source))
    # lru_cache alone allows concurrent cache misses. Serialize initialization
    # so every returned object belongs to the same native class identities.
    with _NATIVE_LOAD_LOCK:
        return _load_native(tuple(sources))


def authority():
    return {'repository': 'The-Interdependency/ucns', 'commit': UCNS_COMMIT,
            'source_sha256s': dict(NATIVE_SOURCES)}


def construct_glyph(character, *, ucns_source_root=None):
    """Admit a scalar at its SPACE-relative bearing before affixiation."""
    return _native(ucns_source_root).attachment_stack.Scalar(character)


def construct_text(text, *, source='uchc:text', placement_radius=1, ucns_source_root=None):
    """Close the supplied scalar occurrences verbatim, including any whitespace."""
    if not isinstance(text, str) or not text:
        raise ValueError('NONEMPTY_TEXT_REQUIRED')
    native = _native(ucns_source_root).attachment_stack
    return native.stack(text, tuple(map(native.Scalar, text)), relation=PROFILE + ':text',
                        source=source, radius=placement_radius)


def construct_sequence(objects, *, source='uchc:sequence', placement_radius=1,
                       bearing='root-endpoint-v1', ucns_source_root=None):
    """Affixiate closed interiors or scalar occurrences at another declared scale."""
    native = _native(ucns_source_root).attachment_stack
    if bearing not in native.POLICIES:
        raise ValueError('UNKNOWN_CLOSED_BEARING')
    if not isinstance(objects, tuple) or not objects:
        raise ValueError('NONEMPTY_IMMUTABLE_PARTICIPANTS_REQUIRED')
    parts = tuple(obj if isinstance(obj, native.Scalar) else native.Closed(obj, bearing)
                  for obj in objects)
    return native.stack('sequence', parts, relation=PROFILE + ':sequence',
                        source=source, radius=placement_radius)


def resultant(obj, *, ucns_source_root=None):
    """Return the exact endpoint expression of a closed stack."""
    if not isinstance(obj, _native(ucns_source_root).attachment_stack.DiskStack):
        raise TypeError('CLOSED_DISC_STACK_REQUIRED')
    return obj.endpoint


def additive_resultant(obj, *, ucns_source_root=None):
    """Return the full native vector the object contributes to another addition."""
    if not isinstance(obj, _native(ucns_source_root).attachment_stack.DiskStack):
        raise TypeError('CLOSED_DISC_STACK_REQUIRED')
    return obj.additive_resultant


def _vector_records(obj):
    return {'placement_endpoint': obj.endpoint.record(),
            'additive_resultant': obj.additive_resultant.record()}


def closed_record(obj, *, ucns_source_root=None):
    """Export one occurrence graph and both exact vector readouts."""
    native = _native(ucns_source_root)
    if not isinstance(obj, native.attachment_stack.DiskStack):
        raise TypeError('CLOSED_DISC_STACK_REQUIRED')
    return {'profile': PROFILE, 'record_version': 2, 'geometry_authority': authority(),
            'graph': native.attachment_codec.export_graph(obj), 'vectors': _vector_records(obj)}


def replay_closed(record, *, ucns_source_root=None):
    """Replay a v1 or v2 graph. Verify every vector declared by v2 records."""
    if not isinstance(record, dict) or record.get('profile') != PROFILE:
        raise ValueError('HALVING_PROVENANCE_MISMATCH')
    graph_fields = {'profile', 'geometry_authority', 'graph'}
    legacy = set(record) == graph_fields
    if legacy:
        expected_authority = {'repository': 'The-Interdependency/ucns', 'commit': _V1_UCNS_COMMIT,
                              'source_sha256s': _V1_NATIVE_SOURCES}
    elif (set(record) == graph_fields | {'record_version', 'vectors'}
          and type(record['record_version']) is int and record['record_version'] == 2):
        expected_authority = authority()
    else:
        raise ValueError('HALVING_RECORD_FORMAT_MISMATCH')
    if record['geometry_authority'] != expected_authority:
        raise ValueError('HALVING_PROVENANCE_MISMATCH')
    native = _native(ucns_source_root)
    root = native.attachment_codec.replay_graph(record['graph'])
    for node in record['graph']['nodes']:
        data = node['construction']
        if data.get('relation') == PROFILE + ':text':
            parts = data['participants']
            if (any(p['kind'] != 'scalar' for p in parts)
                    or ''.join(p['identity'] for p in parts) != data['identity']):
                raise ValueError('HALVING_TEXT_MISMATCH')
        elif (data.get('relation') != PROFILE + ':sequence' or data.get('identity') != 'sequence'
              or any(p['kind'] not in ('closed', 'scalar') for p in data['participants'])):
            raise ValueError('HALVING_CONSTRUCTION_REQUIRED')
    if not legacy and (json.dumps(record['vectors'], sort_keys=True, allow_nan=False)
                       != json.dumps(_vector_records(root), sort_keys=True)):
        raise ValueError('HALVING_VECTOR_MISMATCH')
    return root
# ratios: loc_comments=132:22 imports_exports=8:8 calls_definitions=60:11
