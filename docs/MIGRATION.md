# UCHC migration record

## Candidate

- name: UCHC
- forge: `The-Interdependency/stack`
- current state: `stabilizing`
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

- repository license: unresolved;
- distribution kind and package naming: unresolved;
- immutable release identity: not yet applicable;
- downstream reconsumption: not yet applicable;
- full skill-lib propagation: pending.
