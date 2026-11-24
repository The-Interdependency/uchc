# ratios: loc_comments=105:18 imports_exports=7:7 calls_definitions=49:9
"""UCHC ordinal disc placement. Run `uchc-halving bull` or import construct_text.

Each occurrence retains its Unicode scalar bearing and receives a parent-local
radius from the UCNS disc stack. Completed words retain their interiors.
"""
# === CONTRACTS ===
# id: uchc_recursive_halving
#   given: an ordered nonempty sequence of scalar or closed participants and exact frame radius R
#   then: zero-based occurrence i has radius R/2**(n-i), with replayable order, source and interiors
# === END CONTRACTS ===
from functools import lru_cache
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
import sys
from threading import Lock
from types import ModuleType

PROFILE = 'uchc.ordinal-halving/1'
UCNS_COMMIT = '1be5d4608d7525ca006f8998dbf4db5c08fd8c1b'
NATIVE_SOURCES = {
    'ordinal_affixiation': '35604a2d2226f97ff865ba26e03a0fe99b5062ba7e6e8645051cfcc096a0558d',
    'unicode_gonol': '08eabe18939e775bdd9720538982815a63b300128d70a4cea538a21270f5a597',
    'attachment_stack': 'f3672ae18c95fe17776355aa802b33729e185834006d0fc5d4dc93be304411c4',
    'attachment_codec': 'dc7dc62fda8ba087db1cddf4d2fb72147ec9ccadd694b48fc83d3f25471b9e04',
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


def closed_record(obj, *, ucns_source_root=None):
    """Export all occurrences, sources and shared interiors in native graph order."""
    native = _native(ucns_source_root)
    if not isinstance(obj, native.attachment_stack.DiskStack):
        raise TypeError('CLOSED_DISC_STACK_REQUIRED')
    return {'profile': PROFILE, 'geometry_authority': authority(),
            'graph': native.attachment_codec.export_graph(obj)}


def replay_closed(record, *, ucns_source_root=None):
    """Recompute geometry and validate the complete graph and its profile."""
    if (not isinstance(record, dict) or set(record) != {'profile', 'geometry_authority', 'graph'}
            or record['profile'] != PROFILE or record['geometry_authority'] != authority()):
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
    return root
# ratios: loc_comments=105:18 imports_exports=7:7 calls_definitions=49:9
