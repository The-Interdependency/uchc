# Channel Evidence Inventory

Schema: `uchc.english.channel-evidence-inventory`
Status: inventory only; feeds `inference_v0` channel maps. No winner is picked.

Every field below is classified for use as an inference channel:
`o` (ordinal), `s` (semantic), `c` (context), or `missing` (named refusal, never a skip).

## InferenceFrame fields

| field | native type | channel use | refusal clause if missing |
|---|---|---|---|
| `text` | str | none (source, not an integer channel) | no integer in stored E |
| `source_id` | str | none | no integer in stored E |
| `glyphs[].ordinal` | int | O: gonol-position sum inputs | no integer in stored E |
| `glyphs[].character_id` | int or None | O: first-scalar gonol input | no integer in stored E |
| `glyphs[].utf8_start/end` | int | none (span, not identity) | no integer in stored E |
| `occurrences[].ordinal` | int | O: frame occurrence index; C: sentence position | identity/occurrence collapse |
| `occurrences[].identity_id` | int or None | O: occurrence identity | identity/occurrence collapse |
| `words[].gonol.word_id` | int | O/C inputs | no integer in stored E |
| `words[].definition_ids` | tuple[int] | definition_id unreduced per frame word | no integer in stored E |

## DefinitionRecord fields (per definition_id, unreduced)

| field | native type | channel use | refusal clause if missing |
|---|---|---|---|
| `gonol.definition_id` | int | definition_id (never collapsed) | no integer in stored E |
| `gonol.origin_word_id` | int | O/S/C input | no integer in stored E |
| `gonol.ordinal` | int | O1: definition ordinal | no integer in stored E |
| `gonol.axis_index` | int | S1: source-order index (per def, no winner) | no integer in stored E |
| `definition_index` | int | S3: chain depth | no integer in stored E |
| `previous_definition_id` | int or None | C3: topology as layer-only | not determined |
| `part_of_speech`, `sense_id`, `synset_id` | str | none (non-integer labels) | no integer in stored E |
| `components[].ordinal` | int | S2: component count input | no integer in stored E |
| `components[].identity_id` | int | O3: gonol-position sum; O4: first-scalar gonol; C2: neighbor gonol sum | no integer in stored E |
| `components[].kind` | str | none (word vs character, non-integer) | no integer in stored E |
| `evidence[].target_word_id` | int or None | S: not used in v0 (sense selection not done) | semantic hole |

## Named channel maps (all that the inventory can feed)

O maps:
- `O1.definition_ordinal` — `definition.gonol.ordinal`
- `O2.frame_occurrence_index` — first frame occurrence ordinal of the origin word
- `O3.gonol_position_sum` — sum of component `identity_id`s
- `O4.first_scalar_gonol` — first component `identity_id`

S maps:
- `S1.source_order_index` — 1-based definition index per origin word (per def, no winner)
- `S2.component_count` — number of definition components
- `S3.chain_depth` — `definition_index`
- `S4.refuse_s_zero` — component count with explicit refusal when `s == 0` (semantic hole)

C maps:
- `C1.sentence_position` — frame occurrence ordinal of the origin word
- `C2.neighbor_gonol_sum` — sum of adjacent component `identity_id`s
- `C3.topology_layer_only` — `0` for direct, `definition_index` for chain (layer-only)

## Impossibility clauses (named refusals)

- `no integer in stored E`
- `identity/occurrence collapse`
- `semantic hole`
- `(0,0,0) on real text`
- `not determined`

## Covering d

Recorded per receipt: unset (`None`) AND one bijective d (`158`, congruent to 1 mod 157). No search over d.

## hmmm

- The dead visible ordered-concatenation turn stays inside the composite receipt; it is not the readout.
- No map is declared The Law. Sense selection, learned angles, and canon ratification remain NOT DONE.
