# C++23 source and local bindings

Give the constructor one UTF-8 source file. It retains every physical Unicode
scalar, in order, including the BOM, comments and whitespace. Each occurrence
indexes a shared native UCNS glyph with its exact UTF-32BE diameter, UTF-8
spelling, SPACE-relative bearing and optional Public Gonol position.

The C++23 phase-2 view records physical scalar spans for copied text, the
initial BOM, each CR/LF/CRLF newline, line splices and an implicit final newline.
The physical view can always recover the original bytes. Raw strings retain
their original spelling there. Phase 3 handles raw-string splice reversal and
preprocessing-token recognition. Macros and includes belong to phase 4.
[WG21 N4950, phases of translation](https://timsong-cpp.github.io/cppwp/n4950/lex.phases).

## Run

Install UCHC 0.2.0a5 with the C++ extra from the downloaded wheel. From the
directory containing the wheel and a UTF-8 source file, run:

```sh
python -m pip install './uchc-0.2.0a5-py3-none-any.whl[cpp]'
python -m cpp_gonol build example.cpp example.json
python -m cpp_gonol verify example.json --original example.cpp
python -m cpp_gonol recover example.json recovered.cpp
```

Build and recover write to fresh output paths. Supply `--source-id` for a
portable name when different files share a basename. The standalone Python API
exposes `construct(data, source_id=...)`, `replay(record, original=...)` and
`phase2_text(record)`. The additional `bindings=True` argument or CLI
`--bindings` requires the following language profile.

## Follow an assignment

```cpp
int main() {
    int x = 1;
    { int x = 7; x = x + 1; }
    x = x + 1;
    return x;
}
```

```sh
python -m cpp_gonol build example.cpp binding.json --bindings
python -c 'import json; print(json.load(open("binding.json"))["int_main"]["return_value"])'
```

The inner assignment produces 8. The outer assignment produces 2. The return
reads the outer assignment. Every read records its token ordinal, declaration
and most recent write. Each token points to its original physical glyph
ordinals, including the separate pieces of a spliced identifier. Each
statement records its native frame receipt, lexical scope and ordered tokens.

The admitted grammar has one `int main()` function, nested blocks, initialized
local `int` declarations, assignments, decimal literals, local reads, binary
addition and one final outer `return`. Local names begin with a lowercase
ASCII letter and continue with ASCII letters, digits or underscores. Keywords
and double underscores are excluded. The grammar accepts spaces and C++
comments. Every intermediate value is in the portable inclusive range 0–32767.
Reads before initialization, unknown names, redeclarations in one scope and
unsupported syntax raise an error in binding mode. Physical construction
continues to accept any well-formed UTF-8 source, including ill-formed C++.

The released UCHC ordinal-halving constructor closes a token's scalar discs,
then closes statement, block and function interiors. Each frame retains its
ordered rays and full additive resultant. The `int_main.closed` record
replays with `uchc_halving.replay_closed`. Replaying the encompassing C++
construct also verifies the binding edges and values. A C++ compiler runs
separately on the fixed test programs. [Point of declaration](https://timsong-cpp.github.io/cppwp/n4950/basic.scope.pdecl).

**hmmm** — Macro expansion, general C++ name lookup, types, overload resolution
and execution beyond the declared integer grammar are open.
