# === CHECKS ===
# id: check_hilbert_axes_are_uchc_axes_not_cartesian
#   proves: hilbert_axes_are_uchc_axes_not_cartesian
#   call: self::test_origin_local_basis_uses_declared_axes
#   requires: python3
#   timeout: 30
#   mutates: tmp sqlite only
#   cleanup: pytest tmp_path
#
# id: check_hilbert_axis_identity_is_construct_bound
#   proves: hilbert_axis_identity_is_construct_bound
#   call: self::test_axis_identity_is_construct_bound
#   requires: python3
#   timeout: 30
#   mutates: tmp sqlite only
#   cleanup: pytest tmp_path
#
# id: check_hilbert_origin_local_inner_product
#   proves: hilbert_origin_local_inner_product
#   call: self::test_origin_local_inner_product_and_fail_closed_boundaries
#   requires: python3
#   timeout: 30
#   mutates: tmp sqlite only
#   cleanup: pytest tmp_path
#
# id: check_hilbert_word_promotion_preserves_order_and_multiplicity
#   proves: hilbert_word_promotion_preserves_order_and_multiplicity
#   call: self::test_word_promotion_preserves_order_and_multiplicity
#   requires: python3
#   timeout: 30
#   mutates: tmp sqlite only
#   cleanup: pytest tmp_path
#
# id: check_hilbert_dimension_queries_do_not_reconstruct_members
#   proves: hilbert_dimension_queries_do_not_reconstruct_members
#   call: self::test_dimension_queries_are_direct_counts
#   requires: python3
#   timeout: 30
#   mutates: tmp sqlite only
#   cleanup: pytest tmp_path
#
# id: check_hilbert_finite_origin_spaces_are_complete
#   proves: hilbert_finite_origin_spaces_are_complete
#   call: self::test_finite_spaces_require_explicit_field_and_are_complete
#   requires: python3
#   timeout: 30
#   mutates: tmp sqlite only
#   cleanup: pytest tmp_path
# === END CHECKS ===

from __future__ import annotations

import sqlite3
from hashlib import sha256
from dataclasses import replace
from pathlib import Path

import pytest

from english_gonol.hilbert_inference import (
    ConstructRef,
    VerifiedConstruct,
    HilbertStateVector,
    definition_axis,
    HilbertInferenceError,
    basis_vector,
    definition_promotion,
    definition_space,
    glyph_axis,
    glyph_space,
    word_axis,
    word_promotion,
    word_space,
)
from english_gonol.full_construct_run import _SCHEMA_SQL, _logical_receipt, SCHEMA, VERSION
from english_gonol.hyperspace_construct import (
    glyph_inventory,
    promote_word,
)


def _fixture_db(tmp_path: Path, mutation: str | None = None) -> VerifiedConstruct:
    path = tmp_path / "construct.db"
    db = sqlite3.connect(path)
    db.executescript(_SCHEMA_SQL)
    db.executemany("INSERT INTO meta VALUES (?, ?)", [("schema", SCHEMA), ("version", VERSION)])
    db.executemany(
        "INSERT INTO characters VALUES (?, ?, ?)",
        [(1, "a", 0), (2, "b", 1), (3, " ", 2)],
    )
    db.executemany(
        "INSERT INTO words VALUES (?, ?)",
        [(1, "ab"), (2, "a"), (3, "aa")],
    )
    db.executemany(
        "INSERT INTO word_characters VALUES (?, ?, ?)",
        [
            (1, 0, 1),
            (1, 1, 2),
            (2, 0, 1),
            (3, 0, 1),
            (3, 1, 1),
        ],
    )
    db.execute(
        "INSERT INTO definitions VALUES "
        "(1, 1, 'noun', 1, 'sense', 'synset', 1, 'a a', NULL)"
    )
    db.executemany(
        "INSERT INTO definition_components "
        "(definition_id, ordinal, kind, word_id, character_id, start_offset, end_offset) "
        "VALUES (1, ?, ?, ?, ?, ?, ?)",
        [
            (0, "word", 2, None, 0, 1),
            (1, "character", None, 3, 1, 2),
            (2, "word", 2, None, 2, 3),
        ],
    )
    if mutation:
        db.execute(mutation)
    db.commit()
    logical = _logical_receipt(db)
    db.close()
    ref = ConstructRef(logical, sha256(path.read_bytes()).hexdigest())
    return VerifiedConstruct(path, ref)


def test_origin_local_basis_uses_declared_axes(tmp_path: Path) -> None:
    db = _fixture_db(tmp_path)
    inventory = db.inventory

    a_axis = glyph_axis(inventory["a"], db.construct, db=db)
    b_axis = glyph_axis(inventory["b"], db.construct, db=db)

    assert a_axis.identity == "a"
    assert a_axis.axis_index == inventory["a"].axis_index
    assert a_axis.space_id == "O_G"

    a = basis_vector(a_axis, scalar_field="R")
    b = basis_vector(b_axis, scalar_field="R")
    assert a.inner_product(a) == 1
    assert a.inner_product(b) == 0
    assert a.scale(2).add(b.scale(3)).norm_squared() == 13
    db.close()


def test_axis_identity_is_construct_bound(tmp_path: Path) -> None:
    db = _fixture_db(tmp_path)
    inventory = db.inventory

    same_glyph_a = glyph_axis(inventory["a"], db.construct, db=db)
    other_path = tmp_path / "other"
    other_path.mkdir()
    other = _fixture_db(other_path, "UPDATE words SET surface='ba' WHERE id=1")
    same_glyph_b = glyph_axis(other.inventory["a"], other.construct, db=other)
    assert same_glyph_a != same_glyph_b

    vector_a = basis_vector(same_glyph_a, scalar_field="R")
    vector_b = basis_vector(same_glyph_b, scalar_field="R")
    with pytest.raises(HilbertInferenceError, match="cross-construct"):
        vector_a.inner_product(vector_b)
    other.close()
    db.close()


def test_origin_local_inner_product_and_fail_closed_boundaries(
    tmp_path: Path,
) -> None:
    db = _fixture_db(tmp_path)
    inventory = db.inventory
    glyph = basis_vector(
        glyph_axis(inventory["a"], db.construct, db=db),
        scalar_field="C",
    )
    word, _axis_index = promote_word(db._db, 2)
    word_vector = basis_vector(
        word_axis(word, db.construct, db=db),
        scalar_field="C",
    )

    assert glyph.scale(1j).norm_squared() == 1
    with pytest.raises(HilbertInferenceError, match="cross-origin"):
        glyph.inner_product(word_vector)
    with pytest.raises(HilbertInferenceError, match="scalar fields"):
        glyph.inner_product(
            basis_vector(glyph_axis(inventory["a"], db.construct, db=db), scalar_field="R")
        )
    db.close()


def test_word_promotion_preserves_order_and_multiplicity(tmp_path: Path) -> None:
    db = _fixture_db(tmp_path)
    inventory = db.inventory

    ab = word_promotion(
        db,
        inventory,
        1,
        db.construct,
        scalar_field="R",
    )
    assert [factor.identity for factor in ab.source.factors] == ["a", "b"]
    assert ab.target.identity_kind == "word"
    assert ab.target.identity == "1"

    aa = word_promotion(
        db,
        inventory,
        3,
        db.construct,
        scalar_field="R",
    )
    assert [factor.identity for factor in aa.source.factors] == ["a", "a"]
    assert len(aa.source.factors) == 2
    assert aa.target.identity == "3"

    definition = definition_promotion(
        db,
        inventory,
        1,
        db.construct,
        scalar_field="R",
    )
    assert [
        (factor.identity_kind, factor.identity)
        for factor in definition.source.factors
    ] == [
        ("word", "2"),
        ("glyph", " "),
        ("word", "2"),
    ]
    assert definition.target.space_id == "O_D:1"
    db.close()


def test_dimension_queries_are_direct_counts(tmp_path: Path) -> None:
    db = _fixture_db(tmp_path)
    inventory = db.inventory
    queries: list[str] = []
    db._db.set_trace_callback(queries.append)

    words = word_space(db, db.construct, scalar_field="R")
    definitions = definition_space(db, db.construct, 1, scalar_field="R")
    glyphs = glyph_space(inventory, db.construct, db=db, scalar_field="R")

    db._db.set_trace_callback(None)
    normalized = [" ".join(query.upper().split()) for query in queries]
    assert words.dimension == 3
    assert definitions.dimension == 1
    assert glyphs.dimension == 3
    assert normalized.count("SELECT COUNT(*) FROM WORDS") == 1
    assert normalized.count(
        "SELECT COUNT(*) FROM DEFINITIONS WHERE ORIGIN_WORD_ID = 1"
    ) == 1
    assert not any("WORD_CHARACTERS" in query for query in normalized)
    db.close()


def test_finite_spaces_require_explicit_field_and_are_complete(
    tmp_path: Path,
) -> None:
    db = _fixture_db(tmp_path)
    inventory = db.inventory

    real_space = glyph_space(inventory, db.construct, db=db, scalar_field="R")
    complex_space = word_space(db, db.construct, scalar_field="C")
    assert real_space.complete is True
    assert complex_space.complete is True
    assert real_space.scalar_field == "R"
    assert complex_space.scalar_field == "C"

    with pytest.raises(HilbertInferenceError, match="scalar_field"):
        glyph_space(inventory, db.construct, db=db, scalar_field="Q")
    with pytest.raises(HilbertInferenceError, match="imaginary"):
        basis_vector(
            glyph_axis(inventory["a"], db.construct, db=db),
            scalar_field="R",
        ).scale(1j)
    db.close()


@pytest.mark.parametrize("field", ["artifact_sha256", "logical_receipt"])
def test_rejects_well_formed_false_artifact_identity(tmp_path: Path, field: str) -> None:
    with _fixture_db(tmp_path) as db:
        wrong = replace(db.construct, **{field: "0" * 64})
        with pytest.raises(HilbertInferenceError, match="mismatch"):
            VerifiedConstruct(tmp_path / "construct.db", wrong)


def test_every_database_helper_rejects_stale_reference(tmp_path: Path) -> None:
    with _fixture_db(tmp_path) as db:
        wrong = replace(db.construct, logical_receipt="0" * 64)
        word = promote_word(db._db, 1)[0]
        from english_gonol.hyperspace_construct import promote_definition
        definition = promote_definition(db._db, 1)[0]
        calls = [
            lambda: glyph_axis(db.inventory["a"], wrong, db=db),
            lambda: word_axis(word, wrong, db=db),
            lambda: definition_axis(definition, wrong, db=db),
            lambda: glyph_space(db.inventory, wrong, scalar_field="R", db=db),
            lambda: word_space(db, wrong, scalar_field="R"),
            lambda: definition_space(db, wrong, 1, scalar_field="R"),
            lambda: word_promotion(db, db.inventory, 1, wrong, scalar_field="R"),
            lambda: definition_promotion(db, db.inventory, 1, wrong, scalar_field="R"),
        ]
        for call in calls:
            with pytest.raises(HilbertInferenceError, match="reference does not match"):
                call()
        with pytest.raises(HilbertInferenceError, match="VerifiedConstruct is required"):
            word_space(db._db, db.construct, scalar_field="R")


def test_snapshot_keeps_identity_after_source_changes_and_rejects_closed_handle(tmp_path: Path) -> None:
    with _fixture_db(tmp_path) as db:
        before = word_promotion(db, db.inventory, 1, db.construct, scalar_field="R")
        with sqlite3.connect(tmp_path / "construct.db") as source:
            source.execute("UPDATE words SET surface='ba' WHERE id=1")
        assert word_promotion(db, db.inventory, 1, db.construct, scalar_field="R") == before
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            db._db.execute("UPDATE words SET surface='ba' WHERE id=1")
        with pytest.raises(HilbertInferenceError, match="artifact SHA-256 mismatch"):
            VerifiedConstruct(tmp_path / "construct.db", db.construct)
    with pytest.raises(HilbertInferenceError, match="closed"):
        word_space(db, db.construct, scalar_field="R")


def test_rejects_foreign_glyph_inventory_and_gonols(tmp_path: Path) -> None:
    with _fixture_db(tmp_path) as db:
        foreign = dict(db.inventory)
        foreign["a"] = replace(foreign["a"], axis_index=99)
        with pytest.raises(HilbertInferenceError, match="inventory"):
            word_promotion(db, foreign, 1, db.construct, scalar_field="R")
        with pytest.raises(HilbertInferenceError, match="glyph does not match"):
            glyph_axis(foreign["a"], db.construct, db=db)
        word = promote_word(db._db, 1)[0]
        with pytest.raises(HilbertInferenceError, match="word does not match"):
            word_axis(replace(word, glyph_ids=(2, 1)), db.construct, db=db)


@pytest.mark.parametrize("mutation", [
    "UPDATE words SET surface='ba' WHERE id=1",
    "UPDATE word_characters SET character_id=1 WHERE word_id=1 AND ordinal=1",
    "DELETE FROM word_characters WHERE word_id=1 AND ordinal=1",
])
def test_word_factors_refuse_inconsistent_declared_glyphs(tmp_path: Path, mutation: str) -> None:
    # Hashes are valid for these malformed artifacts; content consistency is a
    # separate obligation, including equal-length disagreement and multiplicity.
    with _fixture_db(tmp_path, mutation) as db:
        with pytest.raises(HilbertInferenceError, match="surface disagrees"):
            word_promotion(db, db.inventory, 1, db.construct, scalar_field="R")


@pytest.mark.parametrize("field, coefficient", [("R", 1e308), ("C", 1e308j)])
def test_inner_product_and_norm_refuse_nonfinite_results(tmp_path: Path, field: str, coefficient: complex) -> None:
    with _fixture_db(tmp_path) as db:
        a = basis_vector(glyph_axis(db.inventory["a"], db.construct, db=db), scalar_field=field)
        enormous = a.scale(coefficient)
        for operation in (lambda: enormous.inner_product(enormous), enormous.norm_squared, enormous.norm):
            with pytest.raises(HilbertInferenceError, match="finite"):
                operation()
        # Each product is finite, but their sum overflows.
        b = basis_vector(glyph_axis(db.inventory["b"], db.construct, db=db), scalar_field=field)
        accumulated = a.add(b).scale(1e154)
        with pytest.raises(HilbertInferenceError, match="finite"):
            accumulated.inner_product(accumulated)


@pytest.mark.parametrize("field", ["R", "C"])
def test_zero_coordinates_have_one_equality_and_hash_identity(tmp_path: Path, field: str) -> None:
    with _fixture_db(tmp_path) as db:
        a = basis_vector(glyph_axis(db.inventory["a"], db.construct, db=db), scalar_field=field)
        zero = HilbertStateVector(db.construct, "O_G", field, ())
        explicit = replace(a, coordinates=((a.coordinates[0][0], -0.0),))
        zeros = (zero, explicit, a.scale(0), a.add(a.scale(-1)), a.scale(1e-300).scale(1e-300))
        assert all(item.coordinates == () and item.norm_squared() == 0 for item in zeros)
        assert len(set(zeros)) == 1
