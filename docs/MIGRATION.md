# UCHC migration record

## Candidate

- name: UCHC
- forge: `The-Interdependency/stack`
- current state: `extracted`; new input-contract release candidate under verification
- intended independent authority: `The-Interdependency/uchc`
- mode: execution

Repository population is authorized by the operator. Implementation/public-contract
authority transfer is **not yet complete**.

## Source baseline

```text
Stack
  ca190204de25de240662bb438af80c8dc405cea6
  research/english-gonol/
  research/python-gonol/

UCNS
  1cf10c2df2541a332a77f2ed3feda0c6bef4abcc

METAPAT
  e4165b0cac9eca41daef9c2f941881028ca55d48

skill-lib
  9a04120686ee4e03338eaf14a81073e467aecfe8
```

## Progress

Historical extraction reported gates 1-5 passed on 2026-09-21. Gate 5
required stronger evidence than the original PYTHONPATH check:

1. source files and tests copied with provenance: done (Stack ca19020);
2. imports/dependencies repaired without semantic redesign: none required;
3. existing local tests pass: English 92 passed, Python 5 passed;
4. replay/receipt behavior matches the pinned forge baseline: English
   hyperspace receipt 38b51ab5..., construct.db sha256 af609bbb...;
5. historical evidence was PYTHONPATH importability, not a clean package install.
   The new root `pyproject.toml` supplies a wheel; clean-install and full-corpus
   acceptance are now executable gates, distinct from the earlier claim.

License gate 6 is resolved. Gates 7-11 (immutable candidate, exact forge
verification, release, reconsumption and authority receipt) remain separate
terminal states. Candidate consumption alone does not transfer authority.

## English

The pinned Stack head contains the implemented
`english_gonol/hyperspace_construct.py` and its tests.

Migration must preserve, at minimum:

- the pinned v2 compact-construct receipt;
- expanded admitted glyph inventory;
- separate carrier-position and axis-participation roles;
- `O_G`, `O_W`, and local `O_D(w)` origins;
- lossless promotion/recovery;
- construction-derived origin attachment;
- cross-frame composition through shared identities;
- exact provenance and replay behavior;
- all surviving `hmmm`.

Do not redesign English during extraction.

## Python

The pinned Stack Python implementation remains the active source. Migration must
preserve exact decoded source occurrences, shared glyph identities, order,
multiplicity, source addresses, control constructions, logical-newline distinctions,
carrier pinning, verification behavior, and unresolved off-carrier cases.

Do not replace construction with tokens or AST nodes; those remain verification
witnesses only.

## Gates before a domain becomes authoritative here

1. source files and tests copied with provenance;
2. imports/dependencies repaired without semantic redesign;
3. existing local tests pass;
4. replay/receipt behavior matches the pinned forge baseline;
5. clean build/install succeeds;
6. license/distribution rights resolved;
7. immutable candidate artifact identified;
8. exact candidate verified in the former forge;
9. verified artifact released;
10. Stack reconsumes that artifact rather than its local implementation;
11. authority-transition receipt recorded.

Until then, Stack remains the implementation owner for that domain.

## hmmm

- repository license: resolved (FSL-1.1-ALv2, licensor The Interdependency LLC, two-year Apache-2.0 conversion);
- candidate package: `uchc`, version `0.1.0a1`, Python wheel; stable publication pending;
- immutable release identity: pending exact-candidate release evidence;
- downstream reconsumption: active Stack ZFAE input consumer under candidate verification;
- full skill-lib propagation: pending.
