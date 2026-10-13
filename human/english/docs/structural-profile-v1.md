# English structural profile v1

Erin Spencer accepted the thirteen structural answers in the 2026-10-10
conversation and requested implementation. This profile is the implementation
of that decision, owned by Stack until UCHC graduation. It supersedes the
non-whitespace-run rule for new structural work. The sealed full-construct v2
builder and consumers remain historical, explicitly versioned evidence.

## Done and failure

Done means exact source is recovered; shared glyph and word identities retain
ordered participations; punctuation and whitespace act outside word identity;
closure and unknown admission remain local; definition relations and original
origins survive; complete OEWN construction and independent replay agree.
Failure includes identity copies caused by repetition, omitted source marks,
unknown words silently admitted by text queries, empty words created by spaces,
ambiguous punctuation guessed closed, or invented UCNS geometry.

## File plan and boundaries

- `english_gonol/structural_rules.py`: deterministic source segmentation and
  punctuation functions. Pure, no network or storage. Tests own adversarial
  boundary examples.
- `english_gonol/structural_construct.py`: complete pinned-corpus construction,
  normalized SQLite identities/participations, replay and command entrypoint.
- `english_gonol/structural_query.py`: read-only text construction against the
  admitted field, atomic promotion, recovery, origins, and named refusals.
- `tests/test_structural_profile.py`: structural and tamper regressions.

New output directories only; never rewrite historical receipts. Rollback is
selecting the historical profile explicitly and removing the new candidate;
no automatic downgrade. No network during construction. Corpus input is public
OEWN data. Query text stays in memory unless a caller explicitly saves it.

## Accepted rules and implementation choices

1. Word boundaries follow glyph function. Unicode letters and combining marks
   form words. Digits participate as numeral characters. Internal apostrophes
   and hyphens remain in a word only between letters/marks; other punctuation
   and all whitespace remain separate. This explicit parser policy is versioned.
2. Every punctuation scalar retains identity, position, and contextual role.
   Decimal dots bind adjacent decimal digits; runs of dots and U+2026 are
   ellipsis, without folding. Abbreviations are derived from exact corpus lexical
   entries plus an explicit case-sensitive conventional list bound into the
   profile. Abbreviation/ellipsis sentence closure stays hmmm unless a caller
   supplies an explicit, provenance-bearing boundary decision.
3. Each ASCII space opens or continues the next unfilled word site. Consecutive
   spaces never create empty word identities. Other whitespace retains its
   scalar and separator function, not an invented circle operation.
4. Full pinned OEWN supplies admission. Queries never grow it implicitly.
5. Repetition adds ordered references to shared identities.
6. Distinct glyph references define the axis set; occurrences define sequence.
   Numeric gonal order stays UCNS-owned and unresolved where no operator exists.
7. Word meanings remain relations to definition constructions; sense and synset
   IDs remain source evidence.
8. Word spans close at licensed separators or end of input; sentence closure is
   separately recorded. Closed words promote atomically with recoverable glyphs.
9. Ambiguity blocks only the dependent closure/geometry operation.
10. Lexical sequences and definitions have source-authorized relations. Arbitrary
    phrase/sentence/recursive promotion requires a named, registered relation
    and its explicit closure conditions; no mandatory ladder or acronym layer.
11. Within a definition, chain means ordered constituent succession and direct
    means each constituent binds to its owner. Existing successive-definition
    chains are preserved separately, never relabeled as constituent chains.
12. Only O_G, O_W and word-local O_D(w) are licensed. Source lexical entries that
    contain several words/punctuation remain exact lexical constructions; their
    assignment to a single word-local definition origin is hmmm. Do not strip
    punctuation and silently attach their meaning to another word.
13. UCNS carrier positions are consumed from exact verified producer bytes.
    Missing displacement, motion and geometric closure operators emit named
    refusals. Logical closure is not geometric execution.

## Runtime

Build actively written SQLite state on a local unsynchronized filesystem. Copy
only closed, verified artifacts into synchronized folders. The local verification
environment replaced open workspace files during synchronization; independent
construction outside that directory passed unchanged.

The complete-corpus replay gate pins Python 3.12.14. SQLite runtime identity is
recorded with verification evidence; changing runtime requires full replay.

## Usage

From `research/english-gonol` (UCHC: set `PYTHONPATH=human/english`):

```bash
python -m english_gonol.structural_construct build \
  --source-root /path/to/oewn/src/yaml \
  --ucns-source-root /path/to/ucns --out-dir /path/to/new-structural-state
python -m english_gonol.structural_construct verify /path/to/new-structural-state
python -m english_gonol.structural_query /path/to/new-structural-state \
  'Dr. creates geometry. Dr. creates 3.14...'
python -m pytest -q tests/test_structural_profile.py
```

Python consumption (one verified field per session):

```python
from english_gonol.structural_query import StructuralField

with StructuralField('/path/to/new-structural-state') as field:
    word = field.word('geometry')
    assert len(word['glyph_axis_set']) == 7
    assert word['occurrence_count'] == 8
    graph = field.construct('Dr.', boundary_decisions={
        '2': {'closed': True, 'source': 'operator:declared-sentence-end'}
    })
    field.replay(graph)
    sentence = field.compose(graph, relation='sentence')
    # Query admission never changes the field; geometry() returns a named
    # UCNS_OPERATION_REQUIRED refusal until the relevant operator is licensed.
```

Explicit boundary decisions are attributed assertions, not independently
verified grammatical evidence. Store their source references with the receipt.
No automatic acronym atom is registered. `ordered-text` and syntactically
closed `sentence` are the query relations; source definitions/lexical sequences
are constructed by the complete-corpus builder.

Replay validates every source construction, all origin/topology bindings,
identity/participation integrity, canonical database rows and manifest fields.
The independent complete rebuild compares canonical graph receipts and database
bytes. A query receipt binds the profile, field receipt, exact input and explicit
boundary decisions; it is not a claim of sentence comprehension.

## hmmm

UCNS displacement/trajectory and geometric gonal order remain unresolved.
Multiword/punctuated lexical entries need an explicitly authorized definition
origin attachment; all their source and definition structure remains preserved.
Parser conventions beyond the accepted thirteen answers are explicit profile
choices, not claims of universally complete English parsing. Graduation and
stable release remain separate work.

## Source-integrity repair and evidence updates

Complete-corpus standing is derived from the pinned source tree, exact counts,
and the ordered SHA-256 of every included native lexeme and synset record.
The digest includes relation fields that do not participate in this construction.
`build(..., complete_corpus=True)` requests that strict gate; callers cannot grant
completeness. Fixture artifacts remain explicitly incomplete. Replay independently
rehashes the included evidence and checks the fixed authority/geometry envelope
and exact carrier producer. A resealed row receipt cannot promote altered source
or manufacture authority transfer.

Sentence composition accepts a contiguous terminal closure cluster (such as `!?`)
followed by the segmenter's permitted closing quote/bracket scalars and trailing
whitespace. These scalars remain ordered participants. Multiple sentences,
separated closing marks, and unresolved abbreviation/ellipsis still refuse.

After implementation changes, rebuild the complete corpus and refresh this
profile's manifest, query and verification receipts together. CI compares its
rebuilt manifest and query with these committed receipts as well as with an
independent rebuild. The work graph pins the immutable repaired source commit;
its descendant evidence commit does not claim a new authority transition.

### Review follow-up boundaries

An explicit `closed: false` decision resolves a nonterminal ambiguity without
creating a sentence boundary. Unresolved ambiguities and nonterminal closed
boundaries still refuse sentence composition. ASCII single quotes share the
same terminal-closing rule as the existing admitted quote/bracket scalars.

Verification checks the exact SQLite table/index definitions and rejects added
columns, views or triggers before a field can be opened. `field.manifest` is a
detached JSON snapshot and `field.abbreviations` is immutable; neither exposes a
mutable alias into the verified receipt/policy inputs. The forge gate compares
all six files in `IMPLEMENTATION_FILES`, including the non-structural runtime
dependencies, plus the extracted structural tests.

The committed verification receipt records a primary local source-versus-clean-wheel replay with Python 3.12.14 and SQLite 3.45.1, matching the hosted runtime versions. CI requires those exact versions and the observed raw database hash. Separately recorded earlier-source artifact 1.0.0 replays with local SQLite 3.53.1 preserve their distinct physical bytes and implementation identities; cross-runtime raw equality failed despite matching canonical manifests and queries, and changing the SQLite writer-version header alone did not explain the difference. No byte normalization is admitted. Hosted replay records actual runtime, checkout identities, artifact hashes and structural test totals in `hosted-replay.json`. Other local domain-suite totals and native attachment checks remain local evidence.

Queries retain the exact verified read transaction until close, including across concurrent SQLite writers and path replacement. Evidence and metadata JSON must match the builder’s canonical encoding. `glyph_axis_set` contains the verified glyph inventory’s O_G axis indexes; ordered glyph identities remain separately recoverable.

### Self-contained raw source evidence (artifact schema 1.1.0)

Complete-corpus standing requires both the pinned projected-record digest and the independently replayed raw OEWN YAML tree. Complete artifacts preserve all 73 source files as bounded canonical `source-file` evidence; pronunciation, examples, source attribution, Wikidata and other unprojected fields remain present as exact bytes. Snapshot-only builds remain explicitly partial even when their projected records match the corpus. Raw paths, encoding, counts, byte budgets and tree digest are checked again during artifact verification, without extracting or executing the payloads.

Raw OEWN evidence retains the upstream Princeton WordNet License and CC BY 4.0 terms named in the repository notice. Distribute data artifacts with the pinned upstream LICENSE.md, README.md and provenance; the structural replay workflow retains that attribution alongside its evidence. The UCHC code license does not replace the corpus licenses.

The implementation identity includes the language package initializer and its complete project-local import-time dependency closure. Manifest bytes themselves must be canonical JSON followed by exactly one newline. CI validates the full extraction receipt envelope and checks out all six declared work-graph participants, recording each observed commit; these provenance checks do not establish semantic or geometry authority.
