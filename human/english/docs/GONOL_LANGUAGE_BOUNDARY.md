# English Gonol language boundary

**Status:** active English Gonol Construction boundary; moved from EDCM without redesign.  
**Authority split:** METAPAT owns affixiation semantics; UCNS owns gonol/Möbius/Public Gonol geometry; English Gonol Construction owns text-domain admission and linguistic/semantic gonol construction; EDCM owns measurement and may evaluate construction outputs.  
**Corrected:** 2026-08-21 after UCNS geometry-only canon and skill-lib `gonol-build` authority repair.

## Governing authorities

The current stack separates meaning, geometry, text construction, and measurement:

```text
METAPAT
    affixiation semantics and relational integration invariants
        ↓
UCNS
    gonol geometry, native Möbius/Public Gonol carrier,
    geometrically established operations
        ↓
English Gonol Construction
    text-domain admission and linguistic/semantic gonol construction
        ↓
EDCM
    measurement and evaluation only; may evaluate English Gonol outputs
    but must not define the construction
```

Authority does not transfer automatically between these layers.

- METAPAT semantic authority does not prove UCNS geometry.
- UCNS geometry does not choose English Gonol text sources, morphology, definitions, or semantic relations.
- English Gonol construction does not validate EDCM measurement.
- EDCM measurement does not validate METAPAT, UCNS, or English Gonol construction.

## Character rule

For active English Gonol text construction:

```text
every admitted character is a gonol
```

This is an English Gonol text-domain rule.

English Gonol Construction owns the declared source/profile that determines what is admitted as a character. A profile may select Unicode code points, graphemes, the exact Public Gonol glyph inventory, or another explicitly defined character unit. If that admission unit is not yet selected for a construction, it remains `hmmm`; UCNS does not silently decide it merely because UCNS supplies the geometry.

Every admitted occurrence remains separately addressable. Repeated characters may share gonol identity where the governing construction says they are the same gonol, while occurrence order, multiplicity, source location, and provenance remain preserved.

## Active text construction

Current English Gonol text construction uses declared scale option sets rather than a mandatory adjacent-scale ladder. Every admitted character is a gonol, but English Gonol Construction must not encode `character -> word -> definition -> recursive` as the only lawful construction path.

Once closed, a gonol is atomic at any scale. Closed gonols may participate directly at any admissible scale without reopening, while identity, order, multiplicity, source positions, relation identity, and provenance remain recoverable.

`edcm.gonol` is the implemented candidate constructor for closing one gonol through a declared scale option set; its constructor identity is retained from the EDCM move for receipt continuity, while the code now lives in `english_gonol.gonol`. Its current option sets include character, word, suffix, suffix-coupling, definition, and recursive relation scales. None is selected canon. UCNS coupling geometry remains `hmmm`, and absent `ucns.public_gonol` does not prevent candidate construction.

When a non-character construction uses a direct source string, each admitted source unit is also closed as a source-character gonol. Those character gonols remain recoverable evidence; they do not force a mandatory adjacent-scale construction ladder.

Relationships that constitute a gonol enter the construction. They are not merely external semantic edges. Sidecars may index, cache, project, or record provenance; they do not replace intrinsic relational content.

## Affixiation

Affixiation is not defined by English Gonol Construction and is not defined by UCNS.

METAPAT defines affixiation as a declared relation among already-bounded participants that preserves their individual addressability, identities, and provenance while the relation may integrate as a higher-scale object-whole. An affixiated whole may participate recursively without erasing its constituents.

UCNS owns any exact geometric realization of that operation. The native Möbius/Public Gonol carrier is the current geometric authority. Where the precise coupling operation has not yet been constructed, it remains `hmmm`; English Gonol Construction must not fill the gap with an invented carrier, topology, scale increment, arity rule, containment rule, or coupling law.

English Gonol Construction applies affixiation to text-domain gonols. Linguistic prefixes and suffixes are one instance of affixiation; they do not define affixiation.

Suffix-coupling options that are suffix-specific are carried by the relevant closed suffix gonol. For example, a closed `ing` suffix gonol may carry `suffix-coupling.vowel-initial = true`. Character-specific behavior is not placed on suffix gonols: final-y rendering belongs to the `y` character gonol's definition-space (`orthographic-behavior:final-y-after-consonant`). `suffixiate()` resolves the interaction between the closed base's final character definitions and the closed suffix's suffix-specific behavior without reopening either gonol.

The complete English root, stem, affix, irregular-transformation, and family law remains unresolved unless source-backed English Gonol evidence establishes it. English Gonol Construction must not invent decomposition to complete a pipeline.

## Public Gonol function positions

UCNS owns the geometry of the exact 157-position Public Gonol carrier and any function operation that geometry actually establishes.

English Gonol Construction may use a Public Gonol position in text construction, but it may not derive the position's operation from Unicode names, dictionary definitions, conventional punctuation grammar, glyph shape, or adjacency. An unresolved operation remains `hmmm`.

When an operation is geometrically authorized, an English Gonol construction must preserve the exact function identity, occurrence address, ordered participants, source/profile identity, carrier/construction identity, result identity, and provenance needed for replay.

## No hidden token or vector layer

English Gonol Construction must not insert conventional NLP token IDs, subword IDs, opaque embedding vectors, or whole-string hashes as substitutes for gonol identity.

Source prose, dictionary material, corpora, labels, and annotations may remain evidence and provenance. Their inclusion does not by itself make them gonol semantics. A text-domain relationship becomes authoritative only through an English Gonol construction whose source, admission, relation, closure, and replay boundaries are explicit.

## Historical evidence

The stack retains sealed historical UCNS/OEWN, lexical-floor, word-gonol, token-named, morphology, and other experiments. Preserve them exactly for reproducibility.

Historical names and producer boundaries remain historical evidence. They do not restore the former rule that UCNS owns lexical construction and they do not override current UCNS geometry-only canon or this English Gonol text-domain boundary.

When reproducing a sealed experiment, use its exact historical commits and artifacts. When beginning new text construction, use the current authority split above.

## EDCM measurement boundary

Construction and measurement remain separate.

EDCM may declare a measurement projection over constructed English Gonol outputs only when the projection, information loss, metric, aggregation, baseline, partitioning, stopping rules, and falsifiers are explicitly frozen as required by the governing experiment.

A reproducible text-gonol construction establishes only that construction. It does not establish semantic quality, compression advantage, reconstruction quality, embedding equivalence, cognition, consciousness, or measurement validity.

## Evidence and replay requirements

A completed text-gonol construction must bind the material identities that determine it, including as applicable:

1. current METAPAT affixiation authority;
2. current UCNS geometric authority;
3. exact English Gonol construction code/profile;
4. exact source artifacts and admission rules;
5. participant identity, occurrence, order, multiplicity, relation identity, scale, and provenance;
6. closure and atomic-participation boundaries;
7. unresolved state and information loss;
8. a deterministic construction receipt; and
9. independent complete reconstruction or replay when completion is claimed.

Preflight real resource requirements before a complete run. Once a healthy admitted run begins, let it reach its natural terminal condition unless a genuine external resource/safety boundary or preregistered load-bearing stopping rule fires.

## Usage guidance

Copy-pasteable unified candidate:

```python
from english_gonol.gonol import construct_gonol, replay_gonol
from english_gonol.language.suffixiation import suffixiate

word = construct_gonol(scale="word", source="try", source_id="example:try")
y_character = word.gonol.source_characters[-1]
construct_gonol(
    scale="definition",
    participants=(y_character,),
    relation="orthographic-behavior:final-y-after-consonant",
    source_id="example:y-orthographic-behavior",
)
ing = construct_gonol(
    scale="suffix",
    source="ing",
    source_id="example:ing",
    carried_options=(("suffix-coupling.vowel-initial", "true"),),
)
definition = construct_gonol(
    scale="definition",
    relation="example:definition-evidence",
    source="to divide with a sharp edge",
    participants=(word.gonol,),
    source_id="example:cut#1",
)
recursive = construct_gonol(
    scale="recursive",
    relation="example:mentions",
    participants=(word.gonol, definition.gonol),
    source_id="example:relation#1",
)
suffix_coupling = suffixiate(word.gonol, ing.gonol, source_id="example:trying#1")
assert recursive.receipt_digest == replay_gonol(receipt=recursive).receipt_digest
assert suffix_coupling.coupling_receipt.receipt_digest == replay_gonol(
    receipt=suffix_coupling.coupling_receipt
).receipt_digest
```

If an explicit `geometry_authority` supplies `PUBLIC_GONOL_157` with a digest matching the pinned Public Gonol identity, `english_gonol.gonol` (constructor identity retained as `edcm.gonol`) observes source-unit positions. If no authority is supplied, construction records geometry as `hmmm` and still closes the candidate. It does not probe ambient imports and does not mutate `sys.path`.

For new text-gonol work:

1. start in English Gonol Construction (`research/english-gonol/`);
2. resolve the exact English Gonol source/admission profile;
3. import current METAPAT affixiation invariants rather than redefining them;
4. consume current UCNS geometry rather than moving text semantics into UCNS;
5. close gonols through declared scale option sets under explicit English Gonol receipts; use `english_gonol.gonol`;
6. keep unresolved UCNS geometric operations as `hmmm`;
7. replay the complete declared construction before claiming completion; and
8. let EDCM freeze any later measurement separately.

For UCNS geometry work, work in UCNS. For changes to the meaning of affixiation, work in METAPAT.

## hmmm

- the exact English Gonol character-admission unit for any source/profile that has not yet selected one;
- the source-supported complete English morphology law;
- the exact UCNS Möbius-carrier affixiation/coupling law exposed by implementation;
- which scale option sets and recursive relations, if any, are later selected, and the exact UCNS geometry for those relations;
- executable direct coupling across distant recursive scales;
- the EDCM projection, information-loss accounting, metric, benchmark, and falsifier for recursive text-gonol evaluation.
