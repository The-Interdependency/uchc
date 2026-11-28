"""Verify the English numerology profile against the 27-bearing atlas walks."""
from copy import deepcopy
from fractions import Fraction
from itertools import combinations
import json
import os

import pytest

from english_gonol.numerology import Numerology, main


@pytest.fixture
def wheel():
    return Numerology(Fraction(3, 2), ucns_source_root=os.environ.get("UCHC_HALVING_UCNS_ROOT"))


def test_integer_and_letter_gonols_retain_identity_at_a_shared_bearing(wheel):
    atoms = [wheel.number(n) for n in (-27, 0, 27, 54)] + [wheel.letter(" "), wheel.letter("0")]
    assert {a.bearing for a in atoms} == {0}
    assert len({a.record()["receipt_sha256"] for a in atoms}) == len(atoms)
    assert [a.face for a in atoms[-2:]] == ["front", "back"]
    assert all(wheel.replay(json.loads(json.dumps(a.record()))) == a for a in atoms)
    assert atoms[2].record()["value"] == {"sign": 1, "digits": [1, 0]}
    huge = wheel.number(-(1 << 15000))
    assert wheel.replay(json.loads(json.dumps(huge.record()))) == huge
    assert wheel.number(-1).bearing == wheel.number(26).bearing == 26
    for bearing, (front, back) in enumerate(zip(" abcdefghijklmnopqrstuvwxyz",
                                                  "0ABCDEFGHIJKLMNOPQRSTUVWXYZ", strict=True)):
        f, b, number = wheel.letter(front), wheel.letter(back), wheel.number(bearing)
        assert f.ray == b.ray == number.ray
        assert f.ray.heading.turn == Fraction(bearing, 27)
        assert f.ray.radius == Fraction(3, 2)
        assert f != b and f != number


STAR_WALKS = (
    (0, 12, 24, 9, 21, 6, 18, 3, 15),
    (1, 13, 25, 10, 22, 7, 19, 4, 16),
    (2, 14, 26, 11, 23, 8, 20, 5, 17),
    (0, 13, 26, 12, 25, 11, 24, 10, 23, 9, 22, 8, 21, 7, 20, 6, 19, 5, 18, 4, 17, 3, 16, 2, 15, 1, 14),
)


@pytest.mark.parametrize("face,alphabet", [("front", " abcdefghijklmnopqrstuvwxyz"),
                                           ("back", "0ABCDEFGHIJKLMNOPQRSTUVWXYZ")])
def test_every_figure_preserves_the_field_walk_and_face(wheel, face, alphabet):
    shapes = [(wheel.triangle(g, face=face), (g % 9, g % 9 + 9, g % 9 + 18))
              for g in range(1, 10)]
    shapes += [(wheel.star(9, i, face=face), STAR_WALKS[i]) for i in range(3)]
    shapes.append((wheel.star(27, face=face), STAR_WALKS[3]))
    for shape, walk in shapes:
        expected = wheel.radius if len(walk) == 3 else wheel.radius / 2
        assert tuple(v.bearing for v in shape.letters) == walk
        assert tuple(v.value for v in shape.letters) == tuple(alphabet[index] for index in walk)
        assert {v.ray.radius for v in shape.letters} == {expected}
        for a, b in combinations(shape.letters, 2):
            assert shape.distance(a.value, b.value) == shape.distance(b.value, a.value) == expected
        assert all(shape.distance(v.value, v.value) == 0 for v in shape.letters)
        angles = sorted(v.ray.heading.turn for v in shape.letters)
        gaps = [(b - a) % 1 for a, b in zip(angles, angles[1:] + angles[:1])]
        assert set(gaps) == {Fraction(1, len(walk))}
        record = shape.record()
        assert Fraction(*record["distinct_pair_distance"]) == expected
        assert wheel.replay(json.loads(json.dumps(record))) == shape
        for edge, source, target in zip(record["edges"], walk, walk[1:] + walk[:1], strict=True):
            assert (edge["from"], edge["to"]) == (source, target)
            octets = [ord(alphabet[source]), ord(alphabet[target])]
            assert edge["ascii_bytes"] == octets
            assert edge["bits"] == " ".join(f"{b:08b}" for b in octets)
    assert sum(len(shape.letters) for shape, _ in shapes) == 81


def test_standalone_star_and_an_explicit_sequence_of_trios(wheel):
    star = wheel.star(9, 1)
    assert wheel.star(27).letters[-1].ray.radius == star.letters[3].ray.radius == wheel.radius / 2
    assert star.distance("a", "p") == wheel.radius / 2
    with pytest.raises(ValueError):
        star.distance("a", "b")
    trios = wheel.letter_trios("amyjvgsdp ")
    assert ["".join(v.value for v in trio) for trio in trios] == ["amy", "jvg", "sdp", " "]
    assert [{v.ray.radius for v in trio} for trio in trios] == [
        {wheel.radius}, {wheel.radius / 2}, {wheel.radius / 4}, {wheel.radius / 8}]


def test_replay_refuses_a_shrinking_star_or_changed_edge(wheel):
    record = wheel.star(9, 1).record()
    altered = deepcopy(record)
    altered["vertices"][3]["ray"]["radius"] = [3, 8]
    with pytest.raises(ValueError, match="reconstructed"):
        wheel.replay(altered)
    altered = deepcopy(record)
    altered["edges"][-1]["to"] = 0
    with pytest.raises(ValueError, match="reconstructed"):
        wheel.replay(altered)


@pytest.mark.parametrize("value", [{"sign": 1, "digits": [0, 1]}, {"sign": 0, "digits": [12]},
                                  {"sign": True, "digits": [1]}, {"sign": 1, "digits": [27]}])
def test_replay_requires_a_canonical_signed_integer(wheel, value):
    record = wheel.number(1).record()
    record["value"] = value
    with pytest.raises(ValueError):
        wheel.replay(record)


def test_unknown_inputs_are_refused(wheel):
    for value in (True, 1.5, "2"):
        with pytest.raises(ValueError):
            wheel.number(value)
    for glyph in ("", "ab", "1", "ë"):
        with pytest.raises(ValueError):
            wheel.letter(glyph)
    for group in (0, 10, True):
        with pytest.raises(ValueError):
            wheel.triangle(group)
    for points, family in ((3, 0), (27, 1), (9, 3), (9, -1), (9, True)):
        with pytest.raises(ValueError):
            wheel.star(points, family)
    with pytest.raises(ValueError):
        wheel.star(9, face="unknown")
    for radius in (0, -1, 0.5, True):
        with pytest.raises(ValueError):
            Numerology(radius, ucns_source_root=os.environ.get("UCHC_HALVING_UCNS_ROOT"))


@pytest.mark.parametrize("args", [("number", "27"), ("letter", "0"), ("triangle", "9", "--face", "back"),
                                 ("star", "9", "--family", "1"), ("star", "27")])
def test_command_emits_replayable_json(wheel, args, capsys):
    producer = os.environ.get("UCHC_HALVING_UCNS_ROOT")
    location = ["--ucns-source-root", producer] if producer else []
    main(["--radius", "3/2", *location, *args])
    record = json.loads(capsys.readouterr().out)
    assert wheel.replay(record).kind == args[0]
