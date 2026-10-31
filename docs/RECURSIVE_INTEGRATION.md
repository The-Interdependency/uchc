# Using the recursive attachment candidate

GPT generated; context, prompt Erin Spencer.

This is the extracted `english.attachment/1` candidate, not a stable release or
an authority graduation. UCNS constructs the geometry; Stack remains the
English forge. The [current extraction](../human/english/experiments/recursive-attachment-v1/extraction.json)
binds its source and tests. The [earlier extraction](../human/english/experiments/recursive-attachment-v1/extraction-86a5fb1.json)
and [October 30 verification](../human/english/experiments/recursive-attachment-v1/local-verification.json)
remain historical evidence.

## Install and use

From the UCHC candidate checkout, with Python 3.12 and Git available:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install 'ucns @ git+https://github.com/The-Interdependency/ucns.git@9cc00771e54336d58ee377faeec87a3a33dbd4bf'
SOURCE_DATE_EPOCH=1790308800 .venv/bin/python -m pip wheel --no-deps . -w dist
.venv/bin/python -m pip install --no-deps dist/uchc-0.1.0a4-py3-none-any.whl
sha256sum dist/uchc-0.1.0a4-py3-none-any.whl
.venv/bin/python -I -m english_gonol.attachment_construction word bull
.venv/bin/python -I -m english_gonol.attachment_construction compound bull shit
.venv/bin/python -I -m english_gonol.attachment_construction sequence bull shit --bearing root-endpoint-v1
.venv/bin/python -I -m english_gonol.attachment_construction sequence bull shit --bearing exit-heading-v1
```

Keep the source commit (`git rev-parse HEAD`) and wheel hash with your outputs.
The module verifies the four pinned UCNS source blobs before constructing.
`-I` prevents a checkout or ambient `PYTHONPATH` from replacing the installed
package. Do not use optimized Python for verification.

`word` accepts an explicitly declared glyph sequence; it does not establish
dictionary admission. `sequence` accepts explicitly separated words; it does
not infer a sentence. Compound joins retain the components' local radii.
Neither bearing candidate is selected as the default.

For corpus admission and sentence closure, use the complete verified structural
field, built with the pinned sources in the
[acceptance workflow](../.github/workflows/english-recursive-attachment.yml):

```python
from english_gonol.attachment_construction import RecursiveStructuralField

with RecursiveStructuralField('/path/to/complete/field',
                              bearing='exit-heading-v1') as field:
    query = field.construct('word word.')
    sentence = field.compose(query, relation='sentence')
    assert sentence['standing'] == 'logically-closed'
    assert sentence['attachment_geometry']['bearing_standing'] == 'unselected-candidate'
```

Omitting `bearing` preserves the word interiors and returns the explicit partial
`CLOSED_WORD_BEARING_POLICY_REQUIRED`. Missing carrier bearings refuse rather
than allocating new angles. `field.definition(record_id)` retains a typed whole
lexical owner, original provenance, parts and succession; it does not claim a
numerical definition attachment.

## Reproduce acceptance

Use the exact Stack commit in the current extraction receipt, not its moving
branch head. From this repository, with that checkout at `/path/to/forge`:

```bash
.venv/bin/python -I tools/verify_attachment_extraction.py /path/to/forge
.venv/bin/python -I -m english_gonol.attachment_audit /path/to/complete/field \
  --expect human/english/experiments/recursive-attachment-v1/corpus-audit.json
```

The complete audit must reproduce 103,027 constructed words, 26 explicit
refusals, and 185,155 definition ownership records, including both ordered stream
digests, exclusions and producer provenance. Equality between two consumers
alone is insufficient: both could share a regression. `--expect` compares the
entire result with the preserved census. Omitting it records a new observation
without claiming baseline acceptance.

The hosted workflow also executes the copied source and installed tests,
compares four CLI operations, and records source, graph, baseline and wheel
identities. Its success must be observed after the jobs actually execute.

## Remaining boundaries

| Requirement | Effect on use |
| --- | --- |
| Closed-word bearing selection | Blocks claiming one canonical bearing. Both named candidates are usable explicitly. |
| Expanded carrier coverage | Blocks constructing the 26 refused corpus words. Does not block the admitted subset. |
| Numerical definition attachment | Blocks definitions-as-geometry. Typed whole-word ownership and provenance remain usable. |
| Punctuation function geometry | Source punctuation and sentence-closure evidence are retained; no punctuation geometry is claimed. |
| Native Möbius/sheet lift | Outside this planar profile; it is not a prerequisite for its bounded use. |
| Hosted verification | Current jobs never start: GitHub reports an account lock due to a billing issue. Local results do not constitute hosted success. |
| Merge and stable publication | UCNS → Stack → UCHC review/merge, exact-candidate forge verification, authorized publication, released-artifact reconsumption and the scoped authority receipt remain separate gates. |

Rollback uses the prior exact candidate wheel or an explicitly versioned
historical profile. It must not reinterpret existing receipts. No consumer
should treat an unmerged branch or a local wheel as a stable released authority.

**hmmm:** billing recovery and executed hosted checks; terminal review and
producer-order merge; stable publication/reconsumption/graduation; the
mathematical boundaries above remain explicit.
