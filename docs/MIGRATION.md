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

## Subsequent Hilbert candidate

Stack PR #65 merged at `6504ed963d93836f66fc88e354fe52809a1a3b7a`, containing
reviewed candidate `2a36a69c30a8395516cf6dc4ffae21ed9908e1bd`. This updates the
Hilbert migration target, not the historical extraction baseline above or the
existing immutable candidate-wheel lock. The shared
[Hilbert work graph](work-graphs/hilbert-inference.json) pins that implementation.

The producer's `research/english-gonol/MIGRATION.json` records `extracted` and
supersedes `GRADUATION.json`. It records existing input-candidate build/forge
verification separately from outstanding stable release, released-artifact
reconsumption, forge-path severance, and scoped authority-transition evidence.
Those input-candidate gates do not establish Hilbert migration or graduation.

UCHC carries only the [provisional migration contract](HILBERT_INFERENCE.md),
including domain-qualified mathematical terms and remaining falsifiers. No
Hilbert implementation or frame bridge is introduced here. To replay or prepare
migration, resolve the exact Stack commit through that graph and run its linked
candidate checks before attempting the lifecycle gates below.

## Recurrence work graph and usage

The [system-set recurrence graph](work-graphs/system-set-recurrence-v0.json)
is the coordination record for agents preparing or reviewing recurrence work
across Stack, UCNS, METAPAT, EDCM and UCHC. Start here before a recurrence replay
or migration: resolve the graph's exact producer commits, inspect the owning
Stack `research/english-gonol/` source and tests, and carry this graph's digest
into any resulting handoff. These are pinned coordination baselines, not claims
that the commits are the latest heads or that downstream validation has passed.

Stack remains the current English semantic-trajectory implementation authority.
UCHC is a migration target only; this record introduces no recurrence code or
public trajectory API. A future migration must first copy source and tests with
provenance, then satisfy the remaining lifecycle gates below. Neither this
graph nor its digest transfers authority, proof, certification, measurement or
empirical standing. All unresolved boundaries remain `hmmm`.

Choose the record by the work being performed, not by its date:

| Record | Scope and relationship |
| --- | --- |
| [inference-input.json](work-graphs/inference-input.json) | Existing input-reader/corpus and candidate-consumption evidence; its pins and receipts remain unchanged. |
| [hilbert-inference.json](work-graphs/hilbert-inference.json) | Subsequent Stack-owned Hilbert migration candidate described above. |
| [system-set-recurrence-v0.json](work-graphs/system-set-recurrence-v0.json) | Recurrence coordination and migration boundary; complements the other graphs and supersedes neither. |

The recurrence graph pins its governing
[skill-lib contract at `38c64332b840b2bbe1c07e53aeee8996644548e9`](https://github.com/The-Interdependency/skill-lib/blob/38c64332b840b2bbe1c07e53aeee8996644548e9/interdependent-work-graph/SKILL.md),
matching the [propagated skills record](../.agents/skills/README.md).
Schema `the-interdependency.stack-manifest` version `1.0.0` hashes exactly
`repositories` and `boundaries` as UTF-8 JSON with sorted object keys, compact
separators and Python's default ASCII escaping. Array order is significant:
preserve the declared METAPAT, UCNS, Stack, UCHC, EDCM, skill-lib order in this
graph, including the order of `hmmm` entries. The digest excludes its own field
and is reproducibility evidence, not producer authentication.

From the repository root, verify the recorded graph digests without changing
files (Python 3.12+, standard library only):

```bash
python3 - <<'PY'
import hashlib, json
from pathlib import Path
paths = sorted(Path('docs/work-graphs').glob('*.json'))
assert paths, 'run from the UCHC repository root'
for path in paths:
    graph = json.loads(path.read_text(encoding='utf-8'))
    assert (graph['schema'], graph['version']) == ('the-interdependency.stack-manifest', '1.0.0'), path
    payload = {key: graph[key] for key in ('repositories', 'boundaries')}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf-8')).hexdigest()
    assert graph['work_graph_sha256'] == digest, f'{path}: digest mismatch'
    print(f'{path}: {digest} verified')
PY
```

To update recurrence provenance, first review the exact changed participant
commits at their owning repositories and preserve their authority and unresolved
boundaries. Edit only the intended graph; do not repin the input or Hilbert
graphs as a side effect. Change the governing skill-lib pin only with an explicit
contract/propagation review. After editing, recompute the recurrence digest:

```bash
python3 - <<'PY'
import hashlib, json, re
from pathlib import Path
path = Path('docs/work-graphs/system-set-recurrence-v0.json')
text = path.read_text(encoding='utf-8')
graph = json.loads(text)
assert (graph['schema'], graph['version']) == ('the-interdependency.stack-manifest', '1.0.0')
payload = {key: graph[key] for key in ('repositories', 'boundaries')}
digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf-8')).hexdigest()
text, count = re.subn(r'("work_graph_sha256"\s*:\s*")[0-9a-f]{64}(")', lambda match: match[1] + digest + match[2], text)
assert count == 1, 'expected one existing SHA-256 digest'
path.write_text(text, encoding='utf-8')
print(digest)
PY
```

Run the read-only verification again and `git diff --check`, then review the
graph and documentation diff together. The **Work-graph integrity** workflow
runs on documentation, propagated-skill and gate changes and checks digests,
the doctrine pin, migration discovery and non-transfer flags at the exact PR
head. It does not run construction or certify migration; implementation changes
still require the separate full-corpus workflow and the lifecycle gates below.

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

- repository license: resolved (FSL-1.1-ALv2, licensor Erin Spencer; each version converts to Apache-2.0 on the second anniversary of the date it is made available);
- candidate package: `uchc`, version `0.1.0a1`, Python wheel; stable publication pending;
- immutable release identity: pending exact-candidate release evidence;
- downstream reconsumption: active Stack ZFAE input consumer under candidate verification;
- full skill-lib propagation: pending.
