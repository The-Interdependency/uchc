# ratios: loc_comments=113:11 imports_exports=9:3 calls_definitions=49:7
# === CONTRACTS ===
# id: cpp23_physical_unicode_replay
#   given: one UTF-8 C++ source file and its ordered native UCNS glyph occurrences
#   then: original bytes and physical-to-phase-2 relations reproduce exactly
# === END CONTRACTS ===
"""C++23 physical glyphs and phase-2 provenance. See construct() and replay()."""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import re

PROFILE = "cpp-gonol.cpp23-utf8/1"
UCNS_COMMIT = "1edfa593ae9d8c9ad394b5462638bcc717f99fbd"
NATIVE_MODULES = {
    "public_gonol": "2da287ce9691b494fc921d14684a3bf7e0633f3a579ea040e3b6ddbaf0d92f27",
    "scalar_bearing": "7d7ff1e1ddbd4997cdbee4f5f17a7c6fa4b8f3d55e288c97f700f610f32be7ac",
    "unicode_gonol": "5360325a51418835f6a4a3c037253ed79b35b2820073cf080ccda9d52cff0c5c",
}
_PHASE_EDGES = re.compile(r"\\[ \t\v\f]*(?:\r\n|[\r\n])|\r\n|[\r\n]")


@lru_cache(maxsize=1)
def _geometry():
    """Check the installed UCNS implementations against the declared producer."""
    for name, digest in NATIVE_MODULES.items():
        module = import_module("ucns." + name)
        if sha256(Path(module.__file__).read_bytes()).hexdigest() != digest:
            raise ValueError(f"UCNS module differs from {UCNS_COMMIT}: {name}")
    from ucns import public_gonol, unicode_gonol
    return public_gonol, unicode_gonol


def _wire(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False,
                      separators=(",", ":"), sort_keys=True).encode("ascii")


def _segments(text):
    """Partition physical scalar ordinals; every deletion has a physical span."""
    spans = []
    cursor = 0
    if text.startswith("\ufeff"):
        spans.append(["bom", 0, 1])
        cursor = 1
    for match in _PHASE_EDGES.finditer(text, cursor):
        start, end = match.span()
        if start > cursor:
            spans.append(["copy", cursor, start])
        kind = "splice" if text[start] == "\\" else "newline"
        spans.append([kind, start, end])
        cursor = end
    if cursor < len(text):
        spans.append(["copy", cursor, len(text)])
    if spans and spans[-1][0] in {"copy", "splice"}:
        spans.append(["implicit-newline", len(text), len(text)])
    return spans


def _project(text, spans, *, positions=False):
    pieces = []
    origins = []
    for kind, start, end in spans:
        if kind == "copy":
            pieces.append(text[start:end])
            if positions:
                origins.extend(range(start, end))
        elif kind in {"newline", "implicit-newline"}:
            pieces.append("\n")
            if positions:
                origins.append(start)
    return "".join(pieces), origins


def construct(data: bytes, *, source_id: str, bindings: bool = False) -> dict:
    """Construct exact UTF-8 bytes; bindings=True adds the qualifying int-main graph."""
    if not isinstance(data, bytes) or not isinstance(source_id, str) or not source_id:
        raise ValueError("immutable source bytes and a nonempty source_id are required")
    if type(bindings) is not bool:
        raise ValueError("bindings must be a boolean")
    source_id.encode("utf-8")
    text = data.decode("utf-8", errors="strict")
    public, native = _geometry()
    glyphs = {}
    for char in sorted(set(text)):
        glyph = native.unicode_glyph_gonol(char)
        glyphs[str(glyph.scalar)] = {
            "utf32be": glyph.utf32_be.hex(),
            "utf8": glyph.utf8.hex(),
            "turn": [glyph.turn.numerator, glyph.turn.denominator],
            "receipt": glyph.receipt,
            "public_position": public.public_gonol_position(char),
        }
    spans = _segments(text)
    translated, origins = _project(text, spans, positions=bindings)
    record = {
        "profile": PROFILE,
        "ucns_commit": UCNS_COMMIT,
        "source_id": source_id,
        "input_bytes": len(data),
        "source_sha256": sha256(data).hexdigest(),
        "glyphs": glyphs,
        "occurrences": list(map(ord, text)),
        "phase2": {"segments": spans, "sha256": sha256(translated.encode()).hexdigest()},
        "int_main": None,
    }
    if bindings:
        from .bindings import int_main
        record["int_main"] = int_main(translated, origins, source_id)
    record["receipt"] = sha256(_wire(record)).hexdigest()
    return record


def replay(record: dict, *, original: bytes | None = None) -> bytes:
    """Recover from native diameters, then rederive the complete record and optional graph."""
    try:
        if record["profile"] != PROFILE:
            raise ValueError("unsupported C++ construct profile")
        table = {key: bytes.fromhex(row["utf32be"]) for key, row in record["glyphs"].items()}
        if any(len(value) != 4 for value in table.values()):
            raise ValueError("invalid UTF-32BE diameter")
        diameters = b"".join(table[str(key)] for key in record["occurrences"])
        data = diameters.decode("utf-32-be", errors="strict").encode("utf-8")
        if original is not None and data != original:
            raise ValueError("construct differs from original source bytes")
        expected = construct(data, source_id=record["source_id"], bindings=record["int_main"] is not None)
        if _wire(expected) != _wire(record):
            raise ValueError("C++ source construct failed exact replay")
    except (AttributeError, KeyError, TypeError, OverflowError) as exc:
        raise ValueError("invalid C++ construct structure") from exc
    return data


def phase2_text(record: dict) -> str:
    """Read the verified C++23 intermediate spelling before preprocessing-token recognition."""
    text = replay(record).decode("utf-8")
    return _project(text, record["phase2"]["segments"])[0]
# ratios: loc_comments=113:11 imports_exports=9:3 calls_definitions=49:7
