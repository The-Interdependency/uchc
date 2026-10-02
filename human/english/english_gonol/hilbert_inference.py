# === MODULE_BUILD ===
# id: uchc_english_hilbert_inference
#   module_name: hilbert_inference
#   module_kind: constructor
#   summary: axis-native Hilbert state contract for English UCHC; admitted glyph axes are basis directions, ordered glyph-axis tensors promote to word axes, and inference frames are ordered tensors of word/glyph axes rather than Cartesian coordinates
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, HilbertInferenceError, AxisRef, HilbertVector, OrderedTensor, AxisPromotion, FiniteHilbertSpace, glyph_axis, word_axis, definition_axis, basis_vector, glyph_space, word_space, definition_space, word_promotion, definition_promotion, frame_basis_state
#   internal_surface: sparse origin-local coordinates, ordered tensor-product basis states, exact identity-preserving promotion
#   auth_boundary: none
#   storage_boundary: no persistent state; consumes verified EnglishConstruct records
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: tests.test_hilbert_inference
#   rollout: use this module to construct the UCHC inference state; inference_v0 and epicyclic consumers remain downstream candidate operators/readouts, not coordinate-system authority
#   rollback: remove this module, its documentation, and tests; existing hyperspace receipts remain unchanged
#   requires: english_gonol_language_hyperspace, uchc_english_inference_input
#   since: 2026-10-01
#   unresolved: canonical scalar field (R or C), cross-origin inner products, amplitude/phase law, sense selection, learned operators, and promotion of a whole sentence into a new axis remain hmmm
# === END MODULE_BUILD ===
#
# === CONTRACTS ===
# id: hilbert_basis_is_uchc_axes_not_cartesian
#   given: an admitted glyph, word, or definition axis
#   then: its basis vector is keyed by that UCHC axis identity; no x/y coordinate basis is introduced
#   class: doctrine
#
# id: hilbert_inner_product_is_origin_local
#   given: vectors in one declared UCHC origin space
#   then: equal basis axes have inner product 1, distinct axes have inner product 0, and cross-origin inner products fail closed
#   class: correctness
#
# id: hilbert_word_promotion_preserves_order_and_multiplicity
#   given: an admitted word gonol
#   then: its source state is the ordered tensor of its glyph-axis basis factors and promotion creates the existing word axis without flattening or deduplicating constituents
#   class: correctness
#
# id: hilbert_frame_state_preserves_occurrence_order
#   given: a complete inference frame
#   then: its state is an ordered tensor of word axes and whitespace glyph axes in exact occurrence order
#   class: correctness
#
# id: hilbert_finite_origin_spaces_are_complete
#   given: the bounded admitted English construct
#   then: each emitted origin-local space is finite-dimensional over R or C and therefore complete
#   class: correctness
# === END CONTRACTS ===

"""Axis-native Hilbert state for English UCHC inference.

The basis is supplied by UCHC axes, not by an external x/y coordinate frame.

At the glyph scale, each admitted glyph axis is a basis direction in H_G.
The ordered glyph-axis factors of a closed word form a basis ket in a tensor
product of H_G; closure then promotes that construction into the word's
existing axis in H_W. Definition constructions analogously consume already
closed word/glyph axes and promote into a word-local definition axis.

An input frame is represented as the ordered tensor of its admitted word axes
and whitespace glyph axes. This preserves identity, order, and multiplicity.
It is not a sense-selection or amplitude law. The canonical scalar field is
not yet selected; origin-local vector operations require callers to state R or C.

Cross-origin inner products remain undefined and fail closed here rather than
silently declaring O_G, O_W, and O_D(w) geometrically orthogonal to one another.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt

from .hyperspace_construct import DefinitionGonol, GlyphGonol, WordGonol
from .inference_input import EnglishConstruct, InferenceFrame

SCHEMA = "uchc.english.hilbert-inference"
VERSION = "0.1.0"


class HilbertInferenceError(ValueError):
    """Raised when an axis/Hilbert operation would invent or lose structure."""


@dataclass(frozen=True, order=True)
class AxisRef:
    """One UCHC basis axis at one declared origin."""

    space_id: str
    identity_kind: str
    identity: str
    axis_index: int

    def __post_init__(self) -> None:
        if not self.space_id:
            raise HilbertInferenceError("space_id must be nonempty")
        if not self.identity_kind:
            raise HilbertInferenceError("identity_kind must be nonempty")
        if not self.identity:
            raise HilbertInferenceError("identity must be nonempty")
        if type(self.axis_index) is not int or self.axis_index < 0:
            raise HilbertInferenceError("axis_index must be a nonnegative integer")

    def as_dict(self) -> dict[str, object]:
        return {
            "space_id": self.space_id,
            "identity_kind": self.identity_kind,
            "identity": self.identity,
            "axis_index": self.axis_index,
        }


def _scalar(value: object, scalar_field: str) -> complex:
    if isinstance(value, bool) or not isinstance(value, (int, float, complex)):
        raise HilbertInferenceError("coefficients must be numeric scalars")
    number = complex(value)
    if not isfinite(number.real) or not isfinite(number.imag):
        raise HilbertInferenceError("coefficients must be finite")
    if scalar_field == "R" and number.imag != 0:
        raise HilbertInferenceError("real Hilbert space rejects imaginary coefficients")
    if scalar_field not in {"R", "C"}:
        raise HilbertInferenceError("scalar_field must be 'R' or 'C'")
    return number


@dataclass(frozen=True)
class HilbertVector:
    """Finite sparse vector over one UCHC origin-local orthonormal basis.

    The scalar field is explicit because the current UCHC construction fixes
    the axes but has not canonized whether inference amplitudes are real or
    complex. Basis identity and promotion are valid in either field.
    """

    space_id: str
    scalar_field: str
    coordinates: tuple[tuple[AxisRef, complex], ...]

    def __post_init__(self) -> None:
        if not self.space_id:
            raise HilbertInferenceError("space_id must be nonempty")
        if self.scalar_field not in {"R", "C"}:
            raise HilbertInferenceError("scalar_field must be 'R' or 'C'")
        seen: set[AxisRef] = set()
        for axis, coefficient in self.coordinates:
            if axis.space_id != self.space_id:
                raise HilbertInferenceError(
                    "vector coordinates must belong to exactly one origin space"
                )
            if axis in seen:
                raise HilbertInferenceError("duplicate axis coordinate")
            seen.add(axis)
            _scalar(coefficient, self.scalar_field)

    @classmethod
    def basis(cls, axis: AxisRef, scalar_field: str) -> "HilbertVector":
        return cls(axis.space_id, scalar_field, ((axis, 1 + 0j),))

    def _map(self) -> dict[AxisRef, complex]:
        return {
            axis: _scalar(value, self.scalar_field)
            for axis, value in self.coordinates
            if value != 0
        }

    def inner_product(self, other: "HilbertVector") -> complex:
        """Origin-local orthonormal-basis inner product.

        Complex spaces conjugate the left argument. Cross-origin products are
        deliberately undefined until UCHC/UCNS license that geometry.
        """

        if not isinstance(other, HilbertVector):
            raise TypeError("other must be HilbertVector")
        if self.space_id != other.space_id:
            raise HilbertInferenceError(
                "cross-origin inner product is hmmm; no geometry is invented here"
            )
        if self.scalar_field != other.scalar_field:
            raise HilbertInferenceError("cannot mix Hilbert scalar fields implicitly")
        left = self._map()
        right = other._map()
        return sum(
            value.conjugate() * right.get(axis, 0j)
            for axis, value in left.items()
        )

    def norm_squared(self) -> float:
        value = self.inner_product(self)
        if value.imag != 0 or value.real < 0:
            raise HilbertInferenceError("inner product produced an invalid norm")
        return float(value.real)

    def norm(self) -> float:
        return sqrt(self.norm_squared())

    def add(self, other: "HilbertVector") -> "HilbertVector":
        if self.space_id != other.space_id:
            raise HilbertInferenceError("cannot add vectors from different origin spaces")
        if self.scalar_field != other.scalar_field:
            raise HilbertInferenceError("cannot mix Hilbert scalar fields implicitly")
        merged = self._map()
        for axis, value in other._map().items():
            merged[axis] = merged.get(axis, 0j) + value
        return HilbertVector(
            self.space_id,
            self.scalar_field,
            tuple(
                (axis, value)
                for axis, value in sorted(merged.items())
                if value != 0
            ),
        )

    def scale(self, scalar: complex) -> "HilbertVector":
        coefficient = _scalar(scalar, self.scalar_field)
        return HilbertVector(
            self.space_id,
            self.scalar_field,
            tuple((axis, coefficient * value) for axis, value in self.coordinates),
        )


@dataclass(frozen=True)
class OrderedTensor:
    """One ordered tensor-product basis state.

    Each factor is already a closed axis at its own admissible scale. The
    ordered factor-space signature is part of the state identity.
    """

    factors: tuple[AxisRef, ...]

    @property
    def space_signature(self) -> tuple[str, ...]:
        return tuple(axis.space_id for axis in self.factors)

    def inner_product(self, other: "OrderedTensor") -> float:
        if not isinstance(other, OrderedTensor):
            raise TypeError("other must be OrderedTensor")
        if self.space_signature != other.space_signature:
            raise HilbertInferenceError(
                "tensor factors inhabit different ordered origin spaces"
            )
        return 1.0 if self.factors == other.factors else 0.0

    def norm(self) -> float:
        return 1.0

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "version": VERSION,
            "space_signature": list(self.space_signature),
            "factors": [axis.as_dict() for axis in self.factors],
        }


@dataclass(frozen=True)
class AxisPromotion:
    """A closed lower-scale tensor promoted into an existing higher-scale axis."""

    relation: str
    source: OrderedTensor
    target: AxisRef

    def as_dict(self) -> dict[str, object]:
        return {
            "relation": self.relation,
            "source": self.source.as_dict(),
            "target": self.target.as_dict(),
        }


@dataclass(frozen=True)
class FiniteHilbertSpace:
    """Bounded origin-local Hilbert-space descriptor.

    Finite-dimensional real or complex inner-product spaces are complete, so
    complete is a derived mathematical property, not a corpus-quality claim.
    """

    space_id: str
    dimension: int
    basis_kind: str
    scalar_field: str
    complete: bool = True

    def __post_init__(self) -> None:
        if not self.space_id or not self.basis_kind:
            raise HilbertInferenceError("space_id and basis_kind must be nonempty")
        if type(self.dimension) is not int or self.dimension < 0:
            raise HilbertInferenceError("dimension must be a nonnegative integer")
        if self.scalar_field not in {"R", "C"}:
            raise HilbertInferenceError("scalar_field must be 'R' or 'C'")

    def as_dict(self) -> dict[str, object]:
        return {
            "space_id": self.space_id,
            "dimension": self.dimension,
            "basis_kind": self.basis_kind,
            "scalar_field": self.scalar_field,
            "complete": self.complete,
        }


def glyph_axis(gonol: GlyphGonol) -> AxisRef:
    return AxisRef("O_G", "glyph", gonol.identity, gonol.axis_index)


def word_axis(gonol: WordGonol) -> AxisRef:
    return AxisRef("O_W", "word", str(gonol.word_id), gonol.axis_index)


def definition_axis(gonol: DefinitionGonol) -> AxisRef:
    return AxisRef(
        f"O_D:{gonol.origin_word_id}",
        "definition",
        str(gonol.definition_id),
        gonol.axis_index,
    )


def basis_vector(axis: AxisRef, *, scalar_field: str) -> HilbertVector:
    return HilbertVector.basis(axis, scalar_field)


def glyph_space(
    corpus: EnglishConstruct, *, scalar_field: str
) -> FiniteHilbertSpace:
    return FiniteHilbertSpace(
        "O_G", len(corpus.inventory), "glyph-axis", scalar_field
    )


def word_space(
    corpus: EnglishConstruct, *, scalar_field: str
) -> FiniteHilbertSpace:
    return FiniteHilbertSpace(
        "O_W",
        sum(1 for _ in corpus.iter_words()),
        "word-axis",
        scalar_field,
    )


def definition_space(
    corpus: EnglishConstruct, word_id: int, *, scalar_field: str
) -> FiniteHilbertSpace:
    word = corpus.word_by_id(word_id)
    return FiniteHilbertSpace(
        f"O_D:{word.gonol.word_id}",
        len(word.definition_ids),
        "definition-axis",
        scalar_field,
    )


def _glyph_factor(corpus: EnglishConstruct, scalar: str) -> AxisRef:
    try:
        gonol = corpus.inventory[scalar]
    except KeyError as exc:
        raise HilbertInferenceError(f"glyph {scalar!r} is not admitted") from exc
    return glyph_axis(gonol)


def word_promotion(corpus: EnglishConstruct, word_id: int) -> AxisPromotion:
    """Promote the ordered glyph-axis construction into the existing word axis."""

    word = corpus.word_by_id(word_id).gonol
    factors = tuple(_glyph_factor(corpus, scalar) for scalar in word.surface)
    if len(factors) != len(word.glyph_ids):
        raise HilbertInferenceError(
            "word surface does not recover the declared glyph multiplicity"
        )
    return AxisPromotion(
        "ordered glyph axes -> closed word axis",
        OrderedTensor(factors),
        word_axis(word),
    )


def definition_promotion(
    corpus: EnglishConstruct, definition_id: int
) -> AxisPromotion:
    """Promote ordered word/glyph component axes into the local definition axis."""

    record = corpus.definition(definition_id)
    factors: list[AxisRef] = []
    for component in record.components:
        if component.kind == "word":
            factors.append(word_axis(corpus.word_by_id(component.identity_id).gonol))
        elif component.kind == "character":
            scalar = record.text[component.start:component.end]
            factors.append(_glyph_factor(corpus, scalar))
        else:
            raise HilbertInferenceError(
                f"unsupported definition component kind {component.kind!r}"
            )
    return AxisPromotion(
        "ordered closed component axes -> definition axis",
        OrderedTensor(tuple(factors)),
        definition_axis(record.gonol),
    )


def frame_basis_state(
    frame: InferenceFrame, corpus: EnglishConstruct
) -> OrderedTensor:
    """Convert a complete input frame to its axis-native tensor basis state.

    Non-whitespace runs already resolve to word identities, so they contribute
    word axes. Whitespace scalars remain glyph identities and contribute glyph
    axes. The tensor preserves exact occurrence order and multiplicity.

    No sentence axis is created here: that promotion relation remains hmmm.
    """

    frame = frame.require_complete()
    if not frame.occurrences:
        raise HilbertInferenceError("empty input has no inference basis state")

    factors: list[AxisRef] = []
    for occurrence in frame.occurrences:
        if occurrence.identity_id is None:
            raise HilbertInferenceError("frame contains an unadmitted occurrence")
        if occurrence.kind == "word":
            factors.append(word_axis(corpus.word_by_id(occurrence.identity_id).gonol))
        elif occurrence.kind == "character":
            factors.append(_glyph_factor(corpus, occurrence.surface))
        else:
            raise HilbertInferenceError(
                f"unsupported occurrence kind {occurrence.kind!r}"
            )
    return OrderedTensor(tuple(factors))


__all__ = [
    "SCHEMA",
    "VERSION",
    "HilbertInferenceError",
    "AxisRef",
    "HilbertVector",
    "OrderedTensor",
    "AxisPromotion",
    "FiniteHilbertSpace",
    "glyph_axis",
    "word_axis",
    "definition_axis",
    "basis_vector",
    "glyph_space",
    "word_space",
    "definition_space",
    "word_promotion",
    "definition_promotion",
    "frame_basis_state",
]
