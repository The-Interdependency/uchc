# ratios: loc_comments=149:11 imports_exports=11:3 calls_definitions=84:12
# === CHECKS ===
# id: cpp23_physical_roundtrip_check
#   proves: cpp23_physical_unicode_replay
#   call: self::SourceTests.test_physical_glyphs_and_independent_positions
#   requires: Python 3.12 and pinned UCNS
# id: cpp23_local_binding_check
#   proves: cpp23_local_binding_relation
#   call: self::BindingTests.test_cpp_compiler_independent_of_constructor
#   requires: Python 3.12, pinned UCNS and a C++23 compiler
# === END CHECKS ===
"""Run python -m unittest discover -s tests with the pinned UCNS and a C++23 compiler."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from cpp_gonol import construct, phase2_text, replay
from cpp_gonol.__main__ import main
from fractions import Fraction
from uchc_halving import replay_closed


def build(data, *, bindings=False):
    return construct(data, source_id="example.cpp", bindings=bindings)


class SourceTests(unittest.TestCase):
    def test_physical_glyphs_and_independent_positions(self):
        source = "\ufeff// e ë e\u0308 🐍 e\r\n".encode()
        record = build(source)
        self.assertEqual(replay(record, original=source), source)
        self.assertEqual(record["occurrences"], list(map(ord, source.decode())))
        self.assertNotEqual(record["glyphs"]["101"]["receipt"], record["glyphs"]["235"]["receipt"])
        self.assertEqual(record["glyphs"][str(ord("🐍"))]["utf32be"], "0001f40d")
        self.assertIsNone(record["glyphs"][str(ord("🐍"))]["public_position"])
        self.assertEqual(record["glyphs"]["32"]["public_position"], 0)
        self.assertEqual(record["glyphs"]["32"]["turn"], [0, 1])
        covered = [i for _, start, end in record["phase2"]["segments"] for i in range(start, end)]
        self.assertEqual(covered, list(range(len(source.decode()))))

    def test_translation_phase_edges(self):
        cases = [
            ("", ""), ("\n", "\n"), ("a\r\nb\rc\n", "a\nb\nc\n"),
            ("\ufeffx\ufeff", "x\ufeff\n"), ("a\\ \t\v\f\r\nb", "ab\n"),
            ("\\\\\n\n", "\\\n"), ("x\n\\\n", "x\n\n"), ("\\\n", "\n"),
            ('R"d(a\\\r\nb)d"', 'R"d(ab)d"\n'), ("#define A 1\r", "#define A 1\n"),
            ("A\\u00EB", "A\\u00EB\n"), ("\x00", "\x00\n"),
        ]
        for physical, phase2 in cases:
            with self.subTest(physical=physical):
                rec = build(physical.encode())
                self.assertEqual(phase2_text(rec), phase2)
                self.assertEqual(replay(rec), physical.encode())
                self.assertIsNone(rec["int_main"])

    def test_invalid_byte_sequences(self):
        for raw in (b"\x80", b"\xc0\xaf", b"\xed\xa0\x80", b"\xf4\x90\x80\x80",
                    b"\xef\xbb", b"// \xeb", b"\xff\xfeA\0"):
            with self.subTest(raw=raw), self.assertRaises(UnicodeDecodeError):
                build(raw)

    def test_corruption_does_not_replay(self):
        source = b"xx\r\n"
        record = build(source)
        for mutate in (
            lambda r: r["occurrences"].pop(), lambda r: r["glyphs"]["120"].update(utf32be="00000079"),
            lambda r: r["glyphs"]["120"].update(turn=[0, 1]), lambda r: r["glyphs"]["120"].update(utf8="ff"),
            lambda r: r["phase2"]["segments"][0].__setitem__(1, False), lambda r: r.update(source_id="else.cpp"),
            lambda r: r.update(profile="python"), lambda r: r.update(receipt="0"*64),
        ):
            with self.subTest(mutate=mutate):
                changed = deepcopy(record)
                mutate(changed)
                with self.assertRaises(ValueError):
                    replay(changed)
        with self.assertRaises(ValueError):
            replay(record, original=b"xx\n")

    def test_cli_recovery_and_no_clobber(self):
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            source, artifact, recovered = [root / p for p in ("a.cpp", "record.json", "copy.cpp")]
            source.write_bytes(b"int main(){return 2;}\r\n")
            main(["build", str(source), str(artifact), "--bindings"])
            main(["verify", str(artifact), "--original", str(source)])
            main(["recover", str(artifact), str(recovered)])
            self.assertEqual(source.read_bytes(), recovered.read_bytes())
            with self.assertRaises(SystemExit):
                main(["recover", str(artifact), str(source)])
            self.assertEqual(source.read_bytes(), recovered.read_bytes())
            self.assertEqual(json.loads(artifact.read_bytes())["int_main"]["return_value"], 2)


class BindingTests(unittest.TestCase):
    def test_reaching_definitions_and_native_graph(self):
        source = b"int main(){int x=1;{int x=7;x=x+1;}x=x+1;return x;}"
        rec = build(source, bindings=True)
        semantics = rec["int_main"]
        decl, inner, inner_write, outer_write, ret = semantics["events"]
        self.assertEqual([e["value"] for e in semantics["events"]], [1, 7, 8, 2, 2])
        for event, definition, prior in ((inner_write, inner, inner), (outer_write, decl, decl),
                                         (ret, decl, outer_write)):
            link, = event["reads"]
            self.assertEqual(link["declaration"], definition["target"])
            self.assertEqual(link["write"], prior["target"])
            origin, = semantics["token_occurrences"][link["token"]]
            self.assertEqual(source[origin:origin + 1], b"x")
        self.assertNotEqual(inner["scope"], decl["scope"])
        root = replay_closed(semantics["closed"])
        self.assertEqual([ray.radius for ray in root.rays], [Fraction(1, 2**i) for i in (5, 4, 3, 2, 1)])
        self.assertEqual(root.participants[-1].interior.participants[2].interior.source, "example.cpp#block[10,23)")
        self.assertEqual(root.additive_resultant.record(), semantics["closed"]["vectors"]["additive_resultant"])
        self.assertEqual("".join(root.recover()), source.decode().replace(" ", ""))
        self.assertEqual(semantics["return_value"], 2)
        self.assertEqual(replay(rec), source)
        for key in ("declaration", "write", "token"):
            altered = deepcopy(rec)
            altered["int_main"]["events"][-1]["reads"][0][key] += 1
            with self.assertRaises(ValueError):
                replay(altered)

    def test_spliced_identifier_addresses_and_punctuation(self):
        source = b"int main(){int va\\\r\nlue=1;return value;}"
        rec = build(source, bindings=True)
        sem = rec["int_main"]
        indices = sem["token_occurrences"][sem["events"][0]["target"]]
        self.assertEqual(bytes(source[i] for i in indices), b"value")
        self.assertGreater(indices[2] - indices[1], 1)
        self.assertEqual(sem["return_value"], 1)
        self.assertEqual(replay(rec), source)

    def test_nonadmitted_programs_preserve_source(self):
        bodies = [
            "return x;", "int x=x;return x;", "int x=1;{int x=x;}return x;",
            "int x=1;int x=2;return x;", "{int y=1;}return y;", "return 08;", "return 01;",
            "return 32767+1;", "return 0x10;", "return 1;return 2;", "{return 2;}", "",
            "if(true){return 2;}return 0;", "int true=2;return true;", "return 1/*",
            "return sizeof(int);", "auto x=1;return x;", "return 1++2;", 'return R"(2)";',
        ]
        for body in bodies:
            with self.subTest(body=body):
                raw = ("int main(){" + body + "}").encode()
                self.assertEqual(replay(build(raw)), raw)
                with self.assertRaises(ValueError):
                    build(raw, bindings=True)
        with self.assertRaises(ValueError):
            build(b"#define X 2\nint main(){return X;}", bindings=True)

    def test_cpp_compiler_independent_of_constructor(self):
        fixtures = [
            ("int x=1;x=x+1;return x;", 2),
            ("int x=1;int y=x;x=2;return y;", 1),
            ("int x=2;{int x=7;x=x+1;}return x;", 2),
            ("int x=2;int y=0;{int x=7;y=x;}return y+x;", 9),
            ("int a=2;{a=a+3;{int a=0;a=a+1;}}return a;", 5),
            ("int va\\\nlue=9;/* + 99 */ return value + 2;", 11),
            ("int x=1; // x=88;\\\n x=77;\nreturn x;", 1),
            ("return 0;", 0),
        ]
        with tempfile.TemporaryDirectory() as temp:
            source, program = Path(temp) / "a.cpp", Path(temp) / "program"
            for body, expected in fixtures:
                with self.subTest(body=body):
                    raw = ("int main(){" + body + "}\n").encode()
                    record = build(raw, bindings=True)
                    source.write_bytes(replay(record, original=raw))
                    subprocess.run([os.environ.get("CXX", "c++"), "-std=c++23", "-pedantic-errors",
                                    str(source), "-o", str(program)], check=True, capture_output=True)
                    status = subprocess.run([str(program)], check=False).returncode
                    self.assertEqual(status, expected)
                    self.assertEqual(record["int_main"]["return_value"], status)
# ratios: loc_comments=149:11 imports_exports=11:3 calls_definitions=84:12
