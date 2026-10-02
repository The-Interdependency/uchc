# UCHC Hilbert inference state

## Domain claim

`Hilbert space`, `basis`, `vector`, `inner product`, and `tensor product` in this
document use their mathematical senses inside UCHC inference. They do not
redefine METAPAT's domain-qualified `Vector` term. METAPAT constrains the
state/vector/transformation boundary; UCNS owns Public Gonol and geometric
construction; UCHC owns the language-state construction described here.

The architectural correction is:

```text
not: glyph -> x/y coordinates -> word embedding

but:

Public Gonol glyph axis
  -> glyph basis ket
  -> ordered glyph-axis tensor
  -> closed word
  -> word axis
  -> ordered higher-scale tensor
```

Composition creates a new admissible axis without destroying the construction
that produced it.

## Hilbert contract

Let `G` be the admitted glyph-axis inventory. For either explicitly selected
scalar field `F ∈ {R, C}`:

\[
H_G(F) = \ell^2(G;F).
\]

The admitted glyph axes form the orthonormal basis

\[
\{|g\rangle : g \in G\},
\qquad
\langle g_i \mid g_j\rangle = \delta_{ij}.
\]

No Cartesian `x`, `y`, or `z` basis is introduced. A glyph's Public Gonol
carrier position and its UCHC basis-axis participation remain distinct roles.

For an admitted word whose exact ordered glyph construction is

\[
w = g_1g_2\ldots g_n,
\]

the pre-promotion word state is the ordered tensor basis ket

\[
|g_1\rangle \otimes |g_2\rangle \otimes \cdots \otimes |g_n\rangle
\in H_G^{\otimes n}.
\]

Order and multiplicity are load-bearing: `ab`, `ba`, and `aa` are different
tensor states. When that construction closes as the admitted word, UCHC
promotes it to the already-declared word axis

\[
|w\rangle \in H_W(F)=\ell^2(W;F).
\]

The promotion preserves the complete lower-scale construction and provenance;
it does not flatten the word into a sum of glyph coordinates.

Definitions repeat the same rule at the next admitted scale. Their ordered
closed word/glyph components form a tensor basis state and promote to the
word-local definition axis

\[
|d\rangle \in H_D(w;F).
\]

A complete `InferenceFrame` is therefore represented by the ordered tensor of
the axes that its exact occurrence stream already supplies:

- non-whitespace admitted runs contribute word axes;
- whitespace scalars contribute glyph axes;
- occurrence order and multiplicity are preserved exactly.

For example, an admitted source shaped as `word₁␠word₂` inhabits the tensor
product component

\[
H_W \otimes H_G \otimes H_W.
\]

A tensor product of Hilbert spaces is itself a Hilbert space. UCHC therefore
does not need to invent Cartesian coordinates to make an inference frame a
Hilbert state.

## What is implemented

`english_gonol.hilbert_inference` provides:

- origin-qualified `AxisRef` basis identities;
- sparse origin-local `HilbertVector` arithmetic;
- explicit `R` or `C` scalar-field selection for vector arithmetic;
- origin-local orthonormal inner products and norms;
- ordered tensor basis states;
- glyph -> word and component -> definition promotion records;
- exact `InferenceFrame` -> tensor-basis-state construction;
- finite-dimensional space descriptors whose completeness follows
  mathematically from finite dimension over `R` or `C`.

The canonical scalar field is deliberately not selected yet. The basis and
promotion structure are valid over either `R` or `C`; code that introduces
actual amplitudes or phase must name its field rather than smuggling that
decision into a default.

Cross-origin inner products are also undefined. In particular, UCHC does not
silently assert a geometric angle between `O_G`, `O_W`, and `O_D(w)`.
Attempting an origin-local vector operation across those spaces fails closed.

## Relation to current inference candidates

`inference_v0.py` and `epicyclic_consumer.py` remain downstream candidate
operators/readouts.

Their `O/S/C` channel triples are not the coordinate basis of the UCHC state.
They may act on, derive from, or measure an admitted Hilbert state only through
a separately licensed relation. This prevents a candidate displacement law
from becoming the definition of the language space merely because it is
currently executable.

## Usage

```python
from english_gonol.hilbert_inference import (
    basis_vector,
    frame_basis_state,
    glyph_axis,
)

frame = construct.resolve_text("alpha beta", source_id="request:1").require_complete()

# Exact input state: ordered word/glyph-axis tensor.
state = frame_basis_state(frame, construct)
print(state.space_signature)

# Origin-local vector arithmetic requires an explicit scalar field.
a_axis = glyph_axis(construct.inventory["a"])
a = basis_vector(a_axis, scalar_field="R")
assert a.inner_product(a) == 1
```

Use `word_promotion(construct, word_id)` when the required object is the exact
ordered glyph-axis tensor together with the word axis it closes into. Use
`definition_promotion` analogously for a definition.

## Failure definition

The implementation is wrong if any of these occur:

1. an external Cartesian basis is substituted for UCHC glyph axes;
2. word construction is flattened so order or multiplicity can disappear;
3. a closed word fails to become its existing word axis;
4. a frame reorders or deduplicates occurrence axes;
5. a cross-origin inner product is silently invented;
6. `R` and `C` coefficients are mixed without an explicit field choice;
7. O/S/C candidate channels are treated as the language-space coordinates.

## hmmm

- canonical scalar field: `R` or `C`;
- cross-origin inner products and angles;
- amplitude and phase assignment;
- sense-selection and learned inference operators;
- whether and under what constitutive relation a complete sentence closes and
  promotes to a sentence axis;
- recursive promotion beyond the currently admitted word/definition scales.

The unresolved pieces are operators or relations over the state. They do not
erase the now-explicit axis-native Hilbert structure of the state itself.
