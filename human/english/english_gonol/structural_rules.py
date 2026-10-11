# ratios: loc_comments=94:17 imports_exports=6:6 calls_definitions=29:7
"""Exact English structural admission rules; see docs/structural-profile-v1.md.

Usage: ``segment('Dr. creates 3.14...')`` preserves all scalar offsets. This
module assigns linguistic roles, never UCNS geometry or implicit word admission.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import unicodedata
from typing import Iterable

# === CONTRACTS ===
# id: structural_exact_participation
#   given: an exact Unicode scalar sequence
#   then: segmentation reconstructs it without normalization or occurrence loss
# id: structural_local_closure
#   given: abbreviation or ellipsis punctuation
#   then: word closure remains separate from unresolved sentence closure
# === END CONTRACTS ===

PROFILE = "english.structural/1"
DEFAULT_ABBREVIATIONS = ("Dr", "Mr", "Mrs", "Ms", "Prof", "Sr", "Jr", "St", "vs", "etc")


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def letter(scalar: str) -> bool:
    return bool(scalar) and unicodedata.category(scalar)[0] in "LM"


def policy(abbreviations: Iterable[str] = DEFAULT_ABBREVIATIONS) -> dict:
    return {"profile": PROFILE, "unicode_version": unicodedata.unidata_version,
            "abbreviations": sorted(set(abbreviations)), "normalization": "none",
            "word_rule": "letters-marks; internal apostrophe/hyphen between letters-marks",
            "punctuation_rule": "scalar roles; decimal adjacency; exact ellipsis; local closure",
            "space_rule": "opens-or-continues-unfilled-site; no-empty-word",
            "axis_rule": "distinct-identities; ordered-participations",
            "origins": ["O_G", "O_W", "O_D(w)"],
            "geometry": "UCNS-owned; missing operations refuse"}


@dataclass(frozen=True)
class Part:
    kind: str
    text: str
    start: int
    end: int
    roles: tuple[str, ...]
    closure: str
    group: tuple[int, int] | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def segment(text: str, abbreviations: Iterable[str] = DEFAULT_ABBREVIATIONS) -> tuple[Part, ...]:
    """Return exact word and scalar participations; sentence closure is a role.

    The grammatical completeness of a sentence is not inferred. A full stop
    licenses syntactic closure only. Ambiguous abbreviations/ellipsis remain
    hmmm; callers may bind independent explicit boundary evidence later.
    """
    if not isinstance(text, str) or any(0xD800 <= ord(c) <= 0xDFFF for c in text):
        raise ValueError("source must contain Unicode scalars")
    abbreviations = frozenset(abbreviations)
    result: list[Part] = []
    i = 0
    while i < len(text):
        start = i
        c = text[i]
        if letter(c):
            i += 1
            while i < len(text):
                if letter(text[i]):
                    i += 1
                elif (text[i] in "'’‐-" and i + 1 < len(text)
                      and letter(text[i - 1]) and letter(text[i + 1])):
                    i += 1
                else:
                    break
            boundary = ("end-of-input" if i == len(text) else
                        "whitespace" if text[i].isspace() else "glyph-boundary")
            result.append(Part("word", text[start:i], start, i, ("lexical",), boundary))
            continue
        group = None
        closure = "not-applicable"
        if c.isspace():
            roles = ("separator", "opens-or-continues-word-site") if c == " " else ("separator",)
        elif c.isdecimal():
            roles = ("numeral-digit",)
        elif c == "…":
            roles, closure, group = ("ellipsis",), "hmmm", (i, i + 1)
        elif c == ".":
            end = i + 1
            while end < len(text) and text[end] == ".":
                end += 1
            if end - i >= 2:
                roles = ("ellipsis",) if end - i >= 3 else ("unresolved-dot-run",)
                for k in range(i, end):
                    result.append(Part("character", ".", k, k + 1, roles, "hmmm", (i, end)))
                i = end
                continue
            if i > 0 and i + 1 < len(text) and text[i - 1].isdecimal() and text[i + 1].isdecimal():
                roles, group = ("decimal-separator",), (i - 1, i + 2)
            elif (result and result[-1].kind == "word" and result[-1].end == i
                  and (result[-1].text in abbreviations or len(result[-1].text) == 1)):
                roles, closure = ("abbreviation",), "hmmm"
            elif i > 0 and (i + 1 == len(text) or text[i + 1].isspace() or text[i + 1] in '\"”’)]}'):
                roles, closure = ("sentence-close",), "closed"
            else:
                roles, closure = ("unresolved-period",), "hmmm"
        elif c in "!?":
            roles, closure = ("sentence-close",), "closed"
        elif unicodedata.category(c).startswith("P"):
            roles = ("punctuation",)
        else:
            roles = ("symbol",)
        result.append(Part("character", c, i, i + 1, roles, closure, group))
        i += 1
    return tuple(result)
# ratios: loc_comments=94:17 imports_exports=6:6 calls_definitions=29:7
