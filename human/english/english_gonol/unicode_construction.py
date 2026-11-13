# ratios: loc_comments=96:47 imports_exports=8:9 calls_definitions=41:11
# === MODULE_BUILD ===
# id: uchc_unicode_bit_radius_consumer
#   module_name: unicode_construction
#   module_kind: adapter
#   summary: UCHC Unicode text and recursive object completion through exact native UCNS geometry
#   owner: Erin Spencer
#   public_surface: construct_glyph, construct_text, construct_sequence, closed_record, replay_closed, encode_text, decode_text, authority, main
#   auth_boundary: exact caller-supplied UCNS source bytes are verified before execution; integrity is not authentication
#   storage_boundary: verifies the complete four-file native source closure before execution; constructed objects remain caller-owned
#   network_boundary: none
#   user_data_boundary: caller text remains local
#   admin_only: false
#   tests: unicode_tests/test_unicode_construction.py
#   rollout: forward Unicode entrypoint; historical corpus receipts retain exact producers
#   rollback: revert this entrypoint and its pin as one change
#   requires: unicode_gonol_geometry, unicode_recursive_geometry
#   unresolved: automatic closed-object bearings and affixiation beyond declared placement; corpus migration and domain graduation
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: uchc_unicode_native_width
#   given: exact Unicode text and the pinned native source
#   then: all glyphs are native UCNS objects with bit radius 16, bit diameter 32 and big-endian scalar bytes; exact UTF-8 anatomy is retained
# id: uchc_unicode_lossless_transport
#   given: arbitrary admitted scalar sequences including nulls, repeated scalars and supplementary-plane scalars
#   then: big-endian transport and recovery preserve all source occurrences and reject invalid widths or scalar values
# id: uchc_unicode_native_integrity
#   given: missing or changed native source bytes
#   then: fail before executing that source rather than guessing geometry or accepting an ambient installation
# id: uchc_unicode_recursive_completion
#   given: native Unicode glyphs, text frames or completed sequences with declared parent placements
#   then: consume the actual objects recursively, preserve every interior and occurrence, and replay the complete native graph with exact provenance
# === END CONTRACTS ===
"""UCHC's forward 16 b rad / 32-bit big-endian scalar entrypoint.

GPT generated; context, prompt Erin Spencer.

Usage::

    python -m english_gonol.unicode_construction 'Aë𐍈' --ucns-source-root /path/to/ucns

UCNS owns every returned gonol, bearing, bit representation and frame. This
adapter admits exact scalar text without normalizing or splitting it. A text
frame preserves its constituents. construct_sequence consumes those objects or
its own completed results with explicit parent bearings; no label is rebuilt as
text. Automatic bearing selection and corpus migration remain separate.
No network access occurs at runtime.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import ModuleType

UCNS_COMMIT = "0bbed0b3ca7ba507101ada6c8019f870499429fe"
UCNS_SOURCE = "src/ucns/unicode_gonol.py"
UCNS_SOURCE_SHA256 = "302cdb12a1314b21a54a84e4263ec7da498b27c3ec3d82758e2b726a90e2252a"
NATIVE_SOURCES = {
    "unicode_gonol": UCNS_SOURCE_SHA256,
    "ordinal_affixiation": "d76656ada0cd464b51e5f3b58041743f0a85ab07ffe5451a5d654c465034d213",
    "attachment_stack": "a68ce6c286345d8e94865ec73f0dff426a24fcba54738113e7a1713387c6c15f",
    "unicode_recursive": "59adf68258324406c55ca5e93dbf4ae30ef6d0f94134a3702346d67d0fcf78d0",
}
PROFILE = "uchc.unicode-bit-radius/1"
RECURSIVE_PROFILE = "uchc.unicode-recursive/1"


@lru_cache(maxsize=1)
def _load_native(sources: tuple) -> ModuleType:
    # All closure bytes have already been verified; no ambient ucns imports.
    name = "_uchc_unicode_native_" + sha256(b''.join(data for _, data in sources)).hexdigest()
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
    sources = []
    for name, expected in NATIVE_SOURCES.items():
        try:
            source = (Path(ucns_source_root) / 'src/ucns' / (name + '.py')).read_bytes()
        except OSError as exc:
            raise ValueError('UCNS_UNICODE_PRODUCER_REQUIRED') from exc
        if sha256(source).hexdigest() != expected:
            raise ValueError("UCNS_UNICODE_PRODUCER_DRIFT")
        sources.append((name, source))
    return _load_native(tuple(sources))


def authority():
    return {"repository": "The-Interdependency/ucns", "commit": UCNS_COMMIT,
            "source": UCNS_SOURCE, "source_sha256": UCNS_SOURCE_SHA256,
            "source_sha256s": {'src/ucns/' + name + '.py': value for name, value in NATIVE_SOURCES.items()}}


def construct_glyph(character, *, ucns_source_root):
    return _native(ucns_source_root).unicode_gonol.unicode_glyph_gonol(character)


def construct_text(text, *, ucns_source_root, placement_radius=1):
    return _native(ucns_source_root).unicode_gonol.build_unicode_scalar_frame(text, radius=placement_radius)


def construct_sequence(objects, *, ucns_source_root, bearings=None, rotations=None,
                       placement_radius=1, relation='declared-sequence', source='uchc:declared-sequence'):
    """Use the same native closure at each caller-declared consuming boundary."""
    return _native(ucns_source_root).unicode_recursive.close_unicode(
        objects, bearings=bearings, rotations=rotations, radius=placement_radius,
        relation=relation, source=source)


def closed_record(obj, *, ucns_source_root):
    native = _native(ucns_source_root).unicode_recursive
    return {'profile': RECURSIVE_PROFILE, 'geometry_authority': authority(),
            'graph': native.export_unicode_graph(obj)}


def replay_closed(record, *, ucns_source_root):
    native = _native(ucns_source_root).unicode_recursive
    if (not isinstance(record, dict) or set(record) != {'profile', 'geometry_authority', 'graph'}
            or record['profile'] != RECURSIVE_PROFILE
            or record['geometry_authority'] != authority()):
        raise ValueError('UNICODE_CONSTRUCTION_PROVENANCE_MISMATCH')
    return native.replay_unicode_graph(record['graph'])


def encode_text(text, *, ucns_source_root):
    """Four big-endian bytes per scalar, no inserted byte-order marker."""
    return construct_text(text, ucns_source_root=ucns_source_root).utf32_be


def decode_text(data, *, ucns_source_root):
    """Recover complete diameters, retaining zero bytes and source U+FEFF."""
    native = _native(ucns_source_root).unicode_gonol
    if not isinstance(data, bytes):
        raise TypeError("encoded text must be immutable bytes")
    width = native.GONOL_BIT_DIAMETER // 8
    if not data or len(data) % width:
        raise ValueError("encoded text must contain complete four-byte gonol diameters")
    return "".join(native.UnicodeGlyphGonol.from_utf32_be(data[i:i + width]).character
                   for i in range(0, len(data), width))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text")
    parser.add_argument("--ucns-source-root", required=True)
    args = parser.parse_args(argv)
    frame = construct_text(args.text, ucns_source_root=args.ucns_source_root)
    print(json.dumps({"profile": PROFILE, "geometry_authority": authority(),
                      "frame": frame.record()}, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
# ratios: loc_comments=96:47 imports_exports=8:9 calls_definitions=41:11
