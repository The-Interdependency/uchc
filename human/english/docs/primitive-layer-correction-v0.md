# Primitive-layer correction and extension — v0

Status: `UNRESOLVED` experimental correction. Standing: implemented
experimental candidate inside English Gonol Construction only. Nothing here is
UCNS geometry canon, an English lexical truth claim, or a cultural/linguistic
canon selection.

## What changed and why

The previous contract carried character-specific final-y behavior on closed
suffix gonols (`suffix-coupling.final-y-after-consonant = preserve-y` on
`ing`). That misplaced a character property on a suffix. This correction
returns the behavior to the primitive layer and extends construction upward
from characters without rebuilding the existing full-corpus machinery.

## Primitive layer

### Character gonols

Characters remain the most primitive admitted gonols. Each admissible character
closes as a `scale="character"` gonol with an exact source identity
(`char:<char>`); each occurrence inside a word remains individually addressable
through the word gonol's recoverable `source_characters`, preserving identity,
order, multiplicity, relation, and provenance.

Every character gonol may have multiple definition gonols sharing that
character gonol as origin. Character definitions are not mutually exclusive:

- `-` carries both `char-class:operator` and `char-class:punctuation`.
- `y` carries both `char-class:vowel` and `char-class:consonant`.
- Letters carry `letter-pronunciation:<name>` definitions.
- `y` carries `orthographic-behavior:final-y-after-consonant` in its own
  definition-space.

### Digits

Each digit is its own primitive character gonol. Each digit receives:

- a `digit-number-name` definition composed from the number name's own word
  gonol, constructed normally from characters
  (`3 -> three -> (t,h,r,e,e)`);
- additional `numerology:<meaning>` definition gonols (candidate evidence,
  not canon).

### Letters

Letters carry their letter identity, pronunciation definition(s), and any
source-backed character-specific orthographic behavior. `y` carries its
final-y behavior in the `y` character gonol's definition-space; it is not
recreated as a global morphology rule during suffixiation.

## Suffixiation

Suffixes close first (`scale="suffix"`) with their own identity, definitions,
behavior, and provenance. Suffixiation is then affixiation between
already-closed gonols:

```text
G(base); affix; G(suffix)
```

- The base contributes its complete closed construction, including its
  constituent characters' definitions and behavior.
- The suffix contributes its own closed construction and suffix-specific
  behavior (for example `suffix-coupling.vowel-initial = true`).
- Neither gonol is reopened. `suffixiate()` reads only recoverable internal
  construction, resolves the interaction, and closes a normal
  `scale="suffix-coupling"` gonol over the two atomic participants.

Final-y resolution is therefore produced by the `y` character gonol's own
definition-space together with the suffix's suffix-specific behavior:

- `try + ing` (vowel-initial, `ing`) -> `preserve-y`
- `try + ed` (vowel-initial, non-`ing`) -> `y-to-i`
- `play + ing` (final `y` after a vowel) -> no final-y rule applies

## Words and definitions

Character gonols affixiate into word gonols; each word gonol is the common
origin of its distinct definition gonols. Definitions are ordinary
`scale="definition"` closures over the word's already-closed constituent
gonols — not pairwise Euclidean orthogonals. Every word occurrence inside
every definition remains attached as its complete word gonol, with its own
definitions available recursively.

## Frozen run

- Module: `english_gonol.primitive_layer_run`
- Receipt: `experiments/primitive-layer-v0.json`
  - character layer: 157 entries, 383 definition receipts,
    `receipt_digest = 0371835d6d51d1b613584417061bd44cb38d5221d6ed05b87c739ee4f8a7284e`
  - Public Gonol coverage: 157/157 glyphs defined
    (`public_gonol_glyph_definition_coverage = complete`), 102 glyphs with
    explicit `definition:hmmm`
  - `primitive:trying` -> `y_realization = preserve-y`
  - `primitive:tried` -> `y_realization = y-to-i`
- Replay:
  `python -m english_gonol.primitive_layer_run --out experiments/primitive-layer-v0.json`

## Public Gonol glyph definitions

Every glyph on the exact 157-position Public Gonol carrier must have a
definition, even if only `hmmm`. The character definition layer closes a
character gonol for every Public Gonol glyph; the carrier identity is held as
a frozen copy whose digest is verified against the pinned constructor
authority `55d10c84…`. Curated glyphs (letters, digits, operators, and
punctuation already in the character definition table) keep their curated
definitions; every remaining Public Gonol glyph receives one explicit
`definition:hmmm` gonol sharing that glyph's character gonol as origin. No
meaning is invented for unresolved glyphs.

## Preserved, not rebuilt

- The full-corpus orthogonal definition affixiation run
  (`experiments/oewn-affixiation-v0`) replays byte-for-byte unchanged.
- The 1-7 hash-carrier sweep control is unchanged (same report digest).
- Constructor closure logic is unchanged; only the corrected contract text and
  examples moved character-specific behavior off suffix gonols.
- Surface-rendering evidence (`rendering.py`) is unchanged; it remains
  evidence, not construction authority, and is not consulted by suffixiation.

## hmmm

- "y would like its belongings returned by ing" — returned: final-y behavior
  now lives in the `y` character gonol definition-space.
- Exact UCNS affixiation geometry remains unresolved; `suffixiate()` closes
  the coupling gonol and records resolution without inventing geometry.
- Pronunciation is currently a letter-name definition only; full
  source-backed pronunciation evidence remains unresolved.
- Numerology definitions are declared candidate evidence; their source
  standing is not canon.
