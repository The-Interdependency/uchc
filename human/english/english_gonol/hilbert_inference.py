# === MODULE_BUILD ===
# id: english_gonol_hilbert_inference_candidate
#   module_name: hilbert_inference
#   module_kind: constructor
#   summary: stack-forged candidate for axis-native Hilbert inference state; existing glyph axes are basis directions, ordered glyph-axis tensors close into existing word axes, and higher-scale constructions consume those closed axes without Cartesian substitution
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, HilbertInferenceError, ConstructRef, VerifiedConstruct, AxisRef, HilbertStateVector, OrderedTensor, AxisPromotion, FiniteHilbertSpace, glyph_axis, word_axis, definition_axis, basis_vector, glyph_space, word_space, definition_space, word_promotion, definition_promotion
#   internal_surface: origin-local sparse coordinates, construct-qualified axis identity, ordered tensor basis states, direct SQL dimension reads
#   auth_boundary: stack-local English Gonol construction candidate; no UCHC authority transfer
#   storage_boundary: read-only SQLite construct consumption; no persistent state
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_hilbert_inference
#   rollout: remain in Stack forge until the UCHC release/reconsumption/authority-transition gates complete
#   rollback: remove this candidate module, its tests and candidate docs; existing hyperspace receipts remain unchanged
#   requires: english_gonol_language_hyperspace
#   since: 2026-10-01
#   unresolved: canonical scalar field (R or C), cross-origin inner products and angles, amplitudes/phases, learned inference operators, sense selection, sentence-axis promotion, and independent UCHC graduation remain hmmm
# === END MODULE_BUILD ===
#
# === CONTRACTS ===
# id: hilbert_axes_are_uchc_axes_not_cartesian
#   given: an admitted glyph, word, or definition axis and an exact construct identity
#   then: its Hilbert basis identity is that construct-qualified axis; no x/y/z basis is inserted
#   class: doctrine
#
# id: hilbert_axis_identity_is_construct_bound
#   given: otherwise equal axis records from distinct construct artifacts
#   then: the axes compare unequal and no vector/tensor operation silently crosses artifacts
#   class: correctness
#
# id: hilbert_origin_local_inner_product
#   given: two state vectors over the same construct, origin space, and explicit scalar field
#   then: equal basis axes have inner product 1 and distinct basis axes have inner product 0
#   class: correctness
#
# id: hilbert_word_promotion_preserves_order_and_multiplicity
#   given: an admitted word gonol
#   then: its source state is the ordered tensor of its glyph-axis factors and its target is the already-declared word axis
#   class: correctness
#
# id: hilbert_dimension_queries_do_not_reconstruct_members
#   given: a request for word or definition Hilbert-space dimension
#   then: dimension is read directly from the verified construct tables without reconstructing every member
#   class: performance
#
# id: hilbert_finite_origin_spaces_are_complete
#   given: one bounded admitted origin basis over explicitly selected R or C
#   then: the emitted finite-dimensional inner-product space is complete
#   class: correctness
# === END CONTRACTS ===

"""Axis-native Hilbert-state candidate for English Gonol inference.

This module is forged in Stack while English Gonol implementation authority
remains stack-local. It does not transfer implementation/public-contract
authority to UCHC.

The basis is not Cartesian. Existing UCHC/English-Gonol axes are the basis:

    admitted glyph axis
        -> ordered glyph-axis tensor
        -> closed word
        -> existing word axis
        -> ordered higher-scale tensor

The lower-scale construction remains recoverable after promotion. A word is
therefore not flattened into a sum of glyph coordinates.

Mathematical vector/Hilbert terminology is domain-qualified by
docs/hilbert-inference.md and does not redefine METAPAT's state-altering
Vector term or UCNS displacement vectors.

The canonical scalar field is unresolved. Callers must explicitly choose
R or C for every emitted space/vector/tensor. Cross-origin and
cross-construct vector inner products fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import isfinite, sqrt
from pathlib import Path
import sqlite3
import tempfile
from types import MappingProxyType
from typing import Mapping

from .full_construct_run import (
    SCHEMA as CONSTRUCT_SCHEMA,
    VERSION as CONSTRUCT_VERSION,
    _assert_schema_boundary,
    _logical_receipt,
)

from .hyperspace_construct import (
    DefinitionGonol,
    GlyphGonol,
    WordGonol,
    glyph_inventory,
    promote_definition,
    promote_word,
)

SCHEMA = "english-gonol.hilbert-inference-candidate"
VERSION = "0.1.0"


class HilbertInferenceError(ValueError):
    """Raised when an operation would invent, mix, or lose Hilbert structure."""


def _sha256(value: str, label: str) -> str:
    if type(value) is not str:
        raise HilbertInferenceError(f"{label} must be a lowercase SHA-256 string")
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise HilbertInferenceError(f"{label} must be a lowercase SHA-256 string")
    return value


def _field(scalar_field: str) -> str:
    if scalar_field not in {"R", "C"}:
        raise HilbertInferenceError("scalar_field must be 'R' or 'C'")
    return scalar_field


def _scalar(value: object, scalar_field: str) -> complex:
    _field(scalar_field)
    if isinstance(value, bool) or not isinstance(value, (int, float, complex)):
        raise HilbertInferenceError("coefficients must be numeric scalars")
    number = complex(value)
    if not isfinite(number.real) or not isfinite(number.imag):
        raise HilbertInferenceError("coefficients must be finite")
    if scalar_field == "R" and number.imag != 0:
        raise HilbertInferenceError("real Hilbert space rejects imaginary coefficients")
    return number


@dataclass(frozen=True, order=True)
class ConstructRef:
    """Exact logical + physical identity of the consumed construct artifact."""

    logical_receipt: str
    artifact_sha256: str

    def __post_init__(self) -> None:
        _sha256(self.logical_receipt, "logical_receipt")
        _sha256(self.artifact_sha256, "artifact_sha256")

    def as_dict(self) -> dict[str, str]:
        return {
            "logical_receipt": self.logical_receipt,
            "artifact_sha256": self.artifact_sha256,
        }


class VerifiedConstruct:
    """Read-only private snapshot, verified once before any axis is emitted.

    Usage: ``with VerifiedConstruct(path, expected_ref) as db:`` then pass
    ``db`` and ``expected_ref`` to helpers. Expected hashes must come from trusted
    evidence. Copying and hashing the same bytes prevents pathname replacement
    from changing the consumed artifact. Source WAL/uncommitted changes are not
    part of the standalone artifact; publish/checkpoint it before opening.
    """

    def __init__(self, path: str | Path, construct: ConstructRef):
        self._db: sqlite3.Connection | None = None
        self._temporary = tempfile.TemporaryDirectory(prefix="hilbert-construct-")
        try:
            target = Path(self._temporary.name) / "construct.db"
            digest = sha256()
            with Path(path).open("rb") as source, target.open("xb") as snapshot:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
                    snapshot.write(chunk)
            if digest.hexdigest() != construct.artifact_sha256:
                raise HilbertInferenceError("construct artifact SHA-256 mismatch")
            db = sqlite3.connect(f"{target.as_uri()}?mode=ro&immutable=1", uri=True)
            self._db = db
            db.execute("PRAGMA trusted_schema=OFF")
            db.execute("PRAGMA query_only=ON")
            _assert_schema_boundary(db)
            if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise HilbertInferenceError("construct integrity check failed")
            if db.execute("PRAGMA foreign_key_check").fetchall():
                raise HilbertInferenceError("construct has dangling references")
            metadata = dict(db.execute("SELECT key, value FROM meta"))
            if (metadata.get("schema"), metadata.get("version")) != (
                CONSTRUCT_SCHEMA, CONSTRUCT_VERSION
            ):
                raise HilbertInferenceError("unsupported construct schema/version")
            if _logical_receipt(db) != construct.logical_receipt:
                raise HilbertInferenceError("construct logical receipt mismatch")
            self._construct = construct
            self._inventory = MappingProxyType(glyph_inventory(db))
        except Exception as exc:
            self.close()
            if isinstance(exc, HilbertInferenceError):
                raise
            raise HilbertInferenceError(f"cannot verify construct: {exc}") from exc

    @property
    def construct(self) -> ConstructRef:
        return self._construct

    @property
    def inventory(self) -> Mapping[str, GlyphGonol]:
        return self._inventory

    def __enter__(self) -> "VerifiedConstruct":
        _verified_db(self, self.construct)
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def close(self) -> None:
        if self._db is not None:
            self._db.close()
            self._db = None
        self._temporary.cleanup()


def _verified_db(db: VerifiedConstruct, construct: ConstructRef) -> sqlite3.Connection:
    if not isinstance(db, VerifiedConstruct):
        raise HilbertInferenceError("a VerifiedConstruct is required")
    if db._db is None:
        raise HilbertInferenceError("verified construct is closed")
    if db.construct != construct:
        raise HilbertInferenceError("reference does not match verified construct")
    return db._db


def _verified_inventory(db: VerifiedConstruct, inventory: Mapping[str, GlyphGonol]) -> None:
    if inventory != db.inventory:
        raise HilbertInferenceError("glyph inventory does not match verified construct")


@dataclass(frozen=True, order=True)
class AxisRef:
    """One construct-qualified basis axis at one declared origin."""

    construct: ConstructRef
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
            "construct": self.construct.as_dict(),
            "space_id": self.space_id,
            "identity_kind": self.identity_kind,
            "identity": self.identity,
            "axis_index": self.axis_index,
        }


@dataclass(frozen=True)
class HilbertStateVector:
    """Finite sparse mathematical vector over one origin-local axis basis."""

    construct: ConstructRef
    space_id: str
    scalar_field: str
    coordinates: tuple[tuple[AxisRef, complex], ...]

    def __post_init__(self) -> None:
        _field(self.scalar_field)
        if not self.space_id:
            raise HilbertInferenceError("space_id must be nonempty")
        seen: set[AxisRef] = set()
        canonical = []
        for axis, coefficient in self.coordinates:
            if axis.construct != self.construct:
                raise HilbertInferenceError(
                    "vector coordinate belongs to a different construct artifact"
                )
            if axis.space_id != self.space_id:
                raise HilbertInferenceError(
                    "vector coordinates must belong to exactly one origin space"
                )
            if axis in seen:
                raise HilbertInferenceError("duplicate axis coordinate")
            seen.add(axis)
            value = _scalar(coefficient, self.scalar_field)
            if value != 0:
                canonical.append((axis, value))
        object.__setattr__(self, "coordinates", tuple(sorted(canonical)))

    @classmethod
    def basis(
        cls, axis: AxisRef, *, scalar_field: str
    ) -> "HilbertStateVector":
        _field(scalar_field)
        return cls(
            construct=axis.construct,
            space_id=axis.space_id,
            scalar_field=scalar_field,
            coordinates=((axis, 1 + 0j),),
        )

    def _map(self) -> dict[AxisRef, complex]:
        return {
            axis: _scalar(value, self.scalar_field)
            for axis, value in self.coordinates
            if value != 0
        }

    def _compatible(self, other: "HilbertStateVector") -> None:
        if not isinstance(other, HilbertStateVector):
            raise TypeError("other must be HilbertStateVector")
        if self.construct != other.construct:
            raise HilbertInferenceError(
                "cross-construct inner product is undefined and fails closed"
            )
        if self.space_id != other.space_id:
            raise HilbertInferenceError(
                "cross-origin inner product is hmmm and fails closed"
            )
        if self.scalar_field != other.scalar_field:
            raise HilbertInferenceError(
                "cannot mix Hilbert scalar fields implicitly"
            )

    def inner_product(self, other: "HilbertStateVector") -> complex:
        """Return the origin-local orthonormal-basis inner product."""

        self._compatible(other)
        left = self._map()
        right = other._map()
        return _scalar(sum(
            value.conjugate() * right.get(axis, 0j)
            for axis, value in left.items()
        ), self.scalar_field)

    def norm_squared(self) -> float:
        value = self.inner_product(self)
        if value.imag != 0 or value.real < 0:
            raise HilbertInferenceError("inner product produced an invalid norm")
        return float(value.real)

    def norm(self) -> float:
        return sqrt(self.norm_squared())

    def add(self, other: "HilbertStateVector") -> "HilbertStateVector":
        self._compatible(other)
        merged = self._map()
        for axis, value in other._map().items():
            merged[axis] = merged.get(axis, 0j) + value
        return HilbertStateVector(
            self.construct,
            self.space_id,
            self.scalar_field,
            tuple(
                (axis, value)
                for axis, value in sorted(merged.items())
                if value != 0
            ),
        )

    def scale(self, scalar: complex) -> "HilbertStateVector":
        coefficient = _scalar(scalar, self.scalar_field)
        return HilbertStateVector(
            self.construct,
            self.space_id,
            self.scalar_field,
            tuple(
                (axis, coefficient * value)
                for axis, value in self.coordinates
            ),
        )


@dataclass(frozen=True)
class OrderedTensor:
    """One ordered tensor-product basis ket over one exact construct."""

    construct: ConstructRef
    scalar_field: str
    factors: tuple[AxisRef, ...]

    def __post_init__(self) -> None:
        _field(self.scalar_field)
        if not self.factors:
            raise HilbertInferenceError("tensor must contain at least one axis factor")
        if any(axis.construct != self.construct for axis in self.factors):
            raise HilbertInferenceError(
                "tensor factors must belong to exactly one construct artifact"
            )

    @property
    def space_signature(self) -> tuple[str, ...]:
        return tuple(axis.space_id for axis in self.factors)

    def inner_product(self, other: "OrderedTensor") -> complex:
        if not isinstance(other, OrderedTensor):
            raise TypeError("other must be OrderedTensor")
        if self.construct != other.construct:
            raise HilbertInferenceError(
                "cross-construct tensor inner product is undefined"
            )
        if self.scalar_field != other.scalar_field:
            raise HilbertInferenceError(
                "cannot mix tensor-product scalar fields implicitly"
            )
        if self.space_signature != other.space_signature:
            raise HilbertInferenceError(
                "tensor factors inhabit different ordered Hilbert spaces"
            )
        return 1 + 0j if self.factors == other.factors else 0j

    def norm(self) -> float:
        return 1.0

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "version": VERSION,
            "construct": self.construct.as_dict(),
            "scalar_field": self.scalar_field,
            "space_signature": list(self.space_signature),
            "factors": [axis.as_dict() for axis in self.factors],
        }


@dataclass(frozen=True)
class AxisPromotion:
    """A closed lower-scale tensor promoted into an existing higher-scale axis."""

    relation: str
    source: OrderedTensor
    target: AxisRef

    def __post_init__(self) -> None:
        if not self.relation:
            raise HilbertInferenceError("promotion relation must be nonempty")
        if self.source.construct != self.target.construct:
            raise HilbertInferenceError(
                "promotion source and target must share construct identity"
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "relation": self.relation,
            "source": self.source.as_dict(),
            "target": self.target.as_dict(),
        }


@dataclass(frozen=True)
class FiniteHilbertSpace:
    """Bounded origin-local Hilbert-space descriptor."""

    construct: ConstructRef
    space_id: str
    dimension: int
    basis_kind: str
    scalar_field: str
    complete: bool = True

    def __post_init__(self) -> None:
        _field(self.scalar_field)
        if not self.space_id or not self.basis_kind:
            raise HilbertInferenceError("space_id and basis_kind must be nonempty")
        if type(self.dimension) is not int or self.dimension < 0:
            raise HilbertInferenceError("dimension must be a nonnegative integer")

    def as_dict(self) -> dict[str, object]:
        return {
            "construct": self.construct.as_dict(),
            "space_id": self.space_id,
            "dimension": self.dimension,
            "basis_kind": self.basis_kind,
            "scalar_field": self.scalar_field,
            "complete": self.complete,
        }


def glyph_axis(gonol: GlyphGonol, construct: ConstructRef, *, db: VerifiedConstruct) -> AxisRef:
    _verified_db(db, construct)
    if db.inventory.get(gonol.identity) != gonol:
        raise HilbertInferenceError("glyph does not match verified construct")
    return AxisRef(
        construct,
        "O_G",
        "glyph",
        gonol.identity,
        gonol.axis_index,
    )


def word_axis(gonol: WordGonol, construct: ConstructRef, *, db: VerifiedConstruct) -> AxisRef:
    connection = _verified_db(db, construct)
    if promote_word(connection, gonol.word_id)[0] != gonol:
        raise HilbertInferenceError("word does not match verified construct")
    return AxisRef(
        construct,
        "O_W",
        "word",
        str(gonol.word_id),
        gonol.axis_index,
    )


def definition_axis(
    gonol: DefinitionGonol, construct: ConstructRef, *, db: VerifiedConstruct
) -> AxisRef:
    connection = _verified_db(db, construct)
    if promote_definition(connection, gonol.definition_id)[0] != gonol:
        raise HilbertInferenceError("definition does not match verified construct")
    return AxisRef(
        construct,
        f"O_D:{gonol.origin_word_id}",
        "definition",
        str(gonol.definition_id),
        gonol.axis_index,
    )


def basis_vector(
    axis: AxisRef, *, scalar_field: str
) -> HilbertStateVector:
    return HilbertStateVector.basis(axis, scalar_field=scalar_field)


def glyph_space(
    inventory: Mapping[str, GlyphGonol],
    construct: ConstructRef,
    *,
    scalar_field: str,
    db: VerifiedConstruct,
) -> FiniteHilbertSpace:
    _verified_db(db, construct)
    _verified_inventory(db, inventory)
    return FiniteHilbertSpace(
        construct,
        "O_G",
        len(inventory),
        "glyph-axis",
        scalar_field,
    )


def word_space(
    db: VerifiedConstruct,
    construct: ConstructRef,
    *,
    scalar_field: str,
) -> FiniteHilbertSpace:
    row = _verified_db(db, construct).execute("SELECT COUNT(*) FROM words").fetchone()
    if row is None:
        raise HilbertInferenceError("word count query returned no row")
    return FiniteHilbertSpace(
        construct,
        "O_W",
        int(row[0]),
        "word-axis",
        scalar_field,
    )


def definition_space(
    db: VerifiedConstruct,
    construct: ConstructRef,
    origin_word_id: int,
    *,
    scalar_field: str,
) -> FiniteHilbertSpace:
    row = _verified_db(db, construct).execute(
        "SELECT COUNT(*) FROM definitions WHERE origin_word_id = ?",
        (origin_word_id,),
    ).fetchone()
    if row is None:
        raise HilbertInferenceError("definition count query returned no row")
    return FiniteHilbertSpace(
        construct,
        f"O_D:{origin_word_id}",
        int(row[0]),
        "definition-axis",
        scalar_field,
    )


def _glyph_factor(
    inventory: Mapping[str, GlyphGonol],
    scalar: str,
    construct: ConstructRef,
    db: VerifiedConstruct,
) -> AxisRef:
    try:
        gonol = inventory[scalar]
    except KeyError as exc:
        raise HilbertInferenceError(f"glyph {scalar!r} is not admitted") from exc
    return glyph_axis(gonol, construct, db=db)


def word_promotion(
    db: VerifiedConstruct,
    inventory: Mapping[str, GlyphGonol],
    word_id: int,
    construct: ConstructRef,
    *,
    scalar_field: str,
) -> AxisPromotion:
    """Promote an exact ordered glyph-axis construction to its word axis."""

    connection = _verified_db(db, construct)
    _verified_inventory(db, inventory)
    word, _axis_index = promote_word(connection, word_id)
    scalars = tuple(_character_scalar(connection, identity) for identity in word.glyph_ids)
    if "".join(scalars) != word.surface:
        raise HilbertInferenceError("word surface disagrees with declared glyph references")
    factors = tuple(
        _glyph_factor(inventory, scalar, construct, db)
        for scalar in scalars
    )
    return AxisPromotion(
        "ordered glyph axes -> closed word axis",
        OrderedTensor(construct, scalar_field, factors),
        word_axis(word, construct, db=db),
    )


def _character_scalar(db: sqlite3.Connection, character_id: int) -> str:
    row = db.execute(
        "SELECT scalar FROM characters WHERE id = ?",
        (character_id,),
    ).fetchone()
    if row is None:
        raise HilbertInferenceError(
            f"character {character_id} is not constructed"
        )
    return str(row[0])


def definition_promotion(
    db: VerifiedConstruct,
    inventory: Mapping[str, GlyphGonol],
    definition_id: int,
    construct: ConstructRef,
    *,
    scalar_field: str,
) -> AxisPromotion:
    """Promote exact ordered closed components to the local definition axis."""

    connection = _verified_db(db, construct)
    _verified_inventory(db, inventory)
    definition, _axis_index = promote_definition(connection, definition_id)
    factors: list[AxisRef] = []
    for kind, identity_id in definition.constituent_ids:
        if kind == "word":
            factors.append(word_promotion(
                db, inventory, identity_id, construct, scalar_field=scalar_field
            ).target)
        elif kind == "character":
            scalar = _character_scalar(connection, identity_id)
            factors.append(_glyph_factor(inventory, scalar, construct, db))
        else:
            raise HilbertInferenceError(
                f"unsupported definition component kind {kind!r}"
            )
    if not factors:
        raise HilbertInferenceError(
            "definition has no admitted component axes"
        )
    return AxisPromotion(
        "ordered closed component axes -> definition axis",
        OrderedTensor(construct, scalar_field, tuple(factors)),
        definition_axis(definition, construct, db=db),
    )


__all__ = [
    "SCHEMA",
    "VERSION",
    "HilbertInferenceError",
    "ConstructRef",
    "VerifiedConstruct",
    "AxisRef",
    "HilbertStateVector",
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
]
