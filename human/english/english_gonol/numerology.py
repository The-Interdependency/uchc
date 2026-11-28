# SPDX-License-Identifier: FSL-1.1-ALv2
"""English numerology on the 27-bearing wheel. Run `python -m english_gonol.numerology --help`.

UCHC selects the identities, walks, and radius for each construction. The
pinned UCNS producer supplies the equidistant carrier and exact rays.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
from string import ascii_lowercase, ascii_uppercase
from typing import TYPE_CHECKING

from uchc_halving import UCNS_COMMIT, _native
from .gonol import canonical_receipt_bytes

if TYPE_CHECKING:
    from ucns.attachment_stack import Ray
    from ucns.ordinal_affixiation import Carrier

PROFILE = "uchc.english-numerology/1"
FRONT = " " + ascii_lowercase
BACK = "0" + ascii_uppercase


def _record(**fields) -> dict:
    payload = {"profile": PROFILE, "ucns_commit": UCNS_COMMIT, **fields}
    return {**payload, "receipt_sha256": sha256(canonical_receipt_bytes(payload)).hexdigest()}


def _integer_digits(value: int) -> dict:
    magnitude = abs(value)
    digits = []
    while magnitude:
        magnitude, digit = divmod(magnitude, 27)
        digits.append(digit)
    return {"sign": (value > 0) - (value < 0), "digits": digits[::-1] or [0]}


def _read_integer(value: dict) -> int:
    if not isinstance(value, dict):
        raise ValueError("signed base-27 digits required")
    sign, digits = value.get("sign"), value.get("digits")
    if type(sign) is not int or sign not in (-1, 0, 1) or not isinstance(digits, list) or not digits:
        raise ValueError("signed base-27 digits required")
    number = 0
    for digit in digits:
        if type(digit) is not int or not 0 <= digit < 27:
            raise ValueError("invalid base-27 digit")
        number = 27 * number + digit
    return sign * number


@dataclass(frozen=True, slots=True)
class Atom:
    """An integer or a face-specific glyph at an exact bearing and radius."""

    kind: str
    value: int | str
    face: str | None
    bearing: int
    ray: Ray

    def record(self) -> dict:
        value = _integer_digits(self.value) if self.kind == "number" else self.value
        return _record(kind=self.kind, value=value, face=self.face,
                       bearing=self.bearing, ray=self.ray.record())


@dataclass(frozen=True, slots=True)
class Figure:
    """A closed walk over a single equidistant field of letter gonols."""

    kind: str
    family: int
    face: str
    stride: int
    letters: tuple[Atom, ...]
    carrier: Carrier

    @property
    def radius(self) -> Fraction:
        return self.letters[0].ray.radius

    def distance(self, left: str, right: str) -> Fraction:
        """Intrinsic distance between two member glyphs on the figure's face."""
        members = {atom.value: FRONT[atom.bearing] for atom in self.letters}
        if left not in members or right not in members:
            raise ValueError("both glyphs must be members of this figure")
        return self.carrier.initial_distance(members[left], members[right], self.radius)

    def record(self) -> dict:
        vertices = [letter.record() for letter in self.letters]
        edges = []
        for source, target in zip(self.letters, self.letters[1:] + self.letters[:1]):
            octets = [ord(source.value), ord(target.value)]
            edges.append({"from": source.bearing, "to": target.bearing, "ascii_bytes": octets,
                          "bits": " ".join(format(octet, "08b") for octet in octets)})
        return _record(kind=self.kind, family=self.family, face=self.face, points=len(vertices),
                       stride=self.stride, vertices=vertices, edges=edges,
                       distinct_pair_distance=[self.radius.numerator, self.radius.denominator])


class Numerology:
    """Construct atoms and figures at a positive exact outer radius."""

    def __init__(self, radius: int | Fraction = 1, *, ucns_source_root=None):
        native = _native(ucns_source_root)
        self._geometry = native.attachment_stack
        self.carrier = native.ordinal_affixiation.Carrier(tuple(FRONT), PROFILE)
        self.radius = self._geometry.Ray(radius, self._geometry.Direction()).radius

    def _atom(self, kind, value, face, bearing, radius):
        heading = self._geometry.Direction(self.carrier.turn(FRONT[bearing]))
        return Atom(kind, value, face, bearing, self._geometry.Ray(radius, heading))

    def number(self, value: int) -> Atom:
        """Keep the full signed integer identity at its residue bearing."""
        if type(value) is not int:
            raise ValueError("number requires an integer")
        return self._atom("number", value, None, value % len(FRONT), self.radius)

    def letter(self, glyph: str) -> Atom:
        """Admit one of the 54 glyphs, including front SPACE and back digit 0."""
        return self._letter_at(glyph, self.radius)

    def _letter_at(self, glyph: str, radius: Fraction) -> Atom:
        if isinstance(glyph, str) and len(glyph) == 1:
            if glyph in FRONT:
                return self._atom("letter", glyph, "front", FRONT.index(glyph), radius)
            if glyph in BACK:
                return self._atom("letter", glyph, "back", BACK.index(glyph), radius)
        raise ValueError("letter requires an English numerology glyph")

    def letter_trios(self, glyphs: str) -> tuple[tuple[Atom, ...], ...]:
        """An explicit letter sequence halves between trios, including a final partial trio."""
        if not isinstance(glyphs, str):
            raise ValueError("letter trios require a glyph string")
        radius = self.radius
        groups = []
        for start in range(0, len(glyphs), 3):
            groups.append(tuple(self._letter_at(glyph, radius) for glyph in glyphs[start:start + 3]))
            radius /= 2
        return tuple(groups)

    def _figure(self, kind, family, start, stride, points, face, radius):
        if face not in ("front", "back"):
            raise ValueError("face must be front or back")
        alphabet = FRONT if face == "front" else BACK
        letters = tuple(self._letter_at(alphabet[(start + i * stride) % len(alphabet)], radius)
                        for i in range(points))
        return Figure(kind, family, face, stride, letters, self.carrier)

    def triangle(self, group: int, *, face: str = "front") -> Figure:
        """Group 1 starts at a. Group 9 starts at the SPACE / 0 bearing."""
        if type(group) is not int or not 1 <= group <= 9:
            raise ValueError("triangle group must be an integer from 1 to 9")
        return self._figure("triangle", group, group % 9, 9, 3, face, self.radius)

    def star(self, points: int, family: int = 0, *, face: str = "front") -> Figure:
        """Nine-point families start at bearings 0, 1, 2. The 27-point star starts at 0."""
        if type(points) is not int or points not in (9, 27):
            raise ValueError("star requires 9 or 27 points")
        if type(family) is not int or not 0 <= family < 27 // points:
            raise ValueError("nine-point families are 0, 1, 2; the 27-point family is 0")
        stride = 12 if points == 9 else 13
        return self._figure("star", family, family, stride, points, face, self.radius / 2)

    def replay(self, record: dict) -> Atom | Figure:
        """Rebuild a record at this outer radius and compare geometry, letters and receipt."""
        if not isinstance(record, dict) or record.get("profile") != PROFILE:
            raise ValueError("English numerology profile required")
        kind = record.get("kind")
        if kind == "number":
            gonol = self.number(_read_integer(record.get("value")))
        elif kind == "letter":
            gonol = self.letter(record.get("value"))
        elif kind == "triangle":
            gonol = self.triangle(record.get("family"), face=record.get("face"))
        elif kind == "star":
            gonol = self.star(record.get("points"), record.get("family"), face=record.get("face"))
        else:
            raise ValueError("unknown numerology gonol kind")
        if canonical_receipt_bytes(record) != canonical_receipt_bytes(gonol.record()):
            raise ValueError("numerology record differs from its reconstructed geometry")
        return gonol


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--radius", type=Fraction, default=Fraction(1), help="outer radius, e.g. 3/2")
    parser.add_argument("--ucns-source-root", help="checkout of the pinned UCNS producer")
    commands = parser.add_subparsers(dest="kind", required=True)
    commands.add_parser("number").add_argument("value", type=int)
    commands.add_parser("letter").add_argument("glyph", help="one glyph; quote a literal space")
    triangle = commands.add_parser("triangle")
    triangle.add_argument("group", type=int, choices=range(1, 10))
    star = commands.add_parser("star")
    star.add_argument("points", type=int, choices=(9, 27))
    star.add_argument("--family", type=int, default=0)
    for shape in (triangle, star):
        shape.add_argument("--face", choices=("front", "back"), default="front")
    args = parser.parse_args(argv)
    try:
        wheel = Numerology(args.radius, ucns_source_root=args.ucns_source_root)
        if args.kind == "number":
            gonol = wheel.number(args.value)
        elif args.kind == "letter":
            gonol = wheel.letter(args.glyph)
        elif args.kind == "triangle":
            gonol = wheel.triangle(args.group, face=args.face)
        else:
            gonol = wheel.star(args.points, args.family, face=args.face)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(gonol.record(), indent=2))


if __name__ == "__main__":
    main()
