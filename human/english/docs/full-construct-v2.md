# English Gonol full construct v2

Status: **SURVIVED full pinned-corpus construction and replay**.

## Scope

Source evidence: Open English WordNet 2025 at
`globalwordnet/english-wordnet@dc343f2683279ecbb13fab4e2fd778d7b162d287`.

Geometry authority consumed: cleaned UCNS Public Gonol carrier at
`The-Interdependency/ucns@4f863ad37096b7baab8f62820ad5cb937b62a3a7`.

The corpus supplies English evidence. UCNS supplies established geometry only.
No unresolved geometric quantity is filled by convention.

## Construction

The construct admits exactly one shared identity for each exact character
scalar and each exact word surface.

```text
character scalar -> one character id
word surface      -> one word id
word              -> ordered character-id references
```

Repeated characters and words reuse identity; order and multiplicity remain in
the consuming construction.

Definitions are constructions, not merely metadata. Every definition retains:

- the single shared origin word;
- its source ordinal;
- direct topology `word -> Dn`;
- chain topology `word -> D1 -> D2 -> ... -> Dn` through
  `previous_definition_id`;
- the exact ordered source components;
- semantic evidence and provenance.

Exact definition components use the already-established construction rule:

```text
maximal non-whitespace run -> shared word identity
whitespace scalar          -> shared character identity
```

Concatenating those components reconstructs the source definition exactly. No
normalization, case folding, punctuation folding, or whitespace loss occurs.

## Evidence channels

The construction keeps three inputs distinct:

1. **ordinal** — source order of the word's definitions;
2. **semantic** — OEWN sense relations, synset relations, and synset membership
   resolved to existing shared word identities;
3. **sentence-context** — the exact ordered components of the definition.

The declared resolution rule is:

> preponderance relative to the rest of the sentence in which the word appears

No numeric weight is invented. The geometry must derive any resulting motion,
direction, distance, or equilibrium.

## Representation

The normalized artifact contains only:

```text
meta
characters
words
word_characters
definitions
definition_components
semantic_evidence
unresolved_semantic_evidence
```

The builder rejects the old architecture: sentence/sense/synset/n-gram
singleton tables, occurrence-object ledgers, closure graphs, synthetic relation
circles, tangency tables, attention/Möbius bookkeeping, and duplicate giant JSON
serialization.

## Full-corpus evidence

GitHub Actions run `34883084372` completed successfully: focused gates, complete
pinned corpus build, logical replay, SQLite integrity, evidence publication, and
artifact retention all passed.

| quantity | value |
|---|---:|
| character identities | 118 |
| word identities | 164,864 |
| word-character references | 1,739,949 |
| definitions | 185,155 |
| definition components | 3,535,375 |
| resolved semantic evidence | 866,183 |
| unresolved semantic evidence | 0 |
| database bytes | 306,331,648 |
| peak RSS | 286,692 KiB |
| build wall time | 1:34.79 |
| SQLite integrity | `ok` |

Logical construction receipt:

`12277b4959c0c72b7af12097b8a77bf91866bbf669e7f4ac07b6a5f1426ebb57`

Raw generated database SHA-256:

`af609bbba504f95e349f3c1a30aa42923acc8e48c1e67bb481521dbf7e49162b`

The generated database is not committed; `manifest.json`, `evidence.json`, and
`build-time.txt` are the compact permanent receipt.

## hmmm

The exact UCNS law mapping ordinal + semantic + sentence-context evidence to
geometric displacement remains unresolved. Consequently the English builder
contains no invented weight, direction, distance, vector, coordinate, center,
radius, tangency, or motion.
