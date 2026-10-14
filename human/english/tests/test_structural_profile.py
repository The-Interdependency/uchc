# ratios: loc_comments=920:197 imports_exports=39:69 calls_definitions=525:83
"""Witnesses for the accepted thirteen-rule profile, including hostile records."""
import base64
from contextlib import closing
from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path
import sqlite3
import shutil
import subprocess
import sys

import pytest

from english_gonol.language.source import LexemeRecord, SenseRecord, SynsetRecord, WordnetSnapshot
from english_gonol.structural_rules import segment, canonical, digest
from english_gonol.structural_construct import StructuralError, build, verify, _manifest
from english_gonol.structural_query import StructuralField
from english_gonol.hyperspace_construct import glyph_inventory

# === CHECKS ===
# id: check_structural_scalar_recovery
#   proves: structural_exact_participation, structural_local_closure
#   call: self::test_exact_scalar_recovery
#   mutates: none
#   cleanup: none
# id: check_structural_atomic_repetition
#   proves: structural_shared_atomic_words, structural_atomic_recovery
#   call: self::test_repetition_and_atomic_promotion
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_structural_origins
#   proves: structural_definitions_and_origins
#   call: self::test_definition_topologies_and_origins
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_structural_queries
#   proves: structural_queries_do_not_admit, structural_geometry_refuses
#   call: self::test_admission_and_geometry_refusals
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_structural_replay
#   proves: structural_complete_replay
#   call: self::test_complete_rebuild_and_tamper
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_structural_query_snapshot
#   proves: structural_queries_keep_verified_snapshot
#   call: self::test_external_changes_cannot_replace_verified_query_rows
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_structural_snapshot_cleanup
#   proves: structural_queries_keep_verified_snapshot
#   call: self::test_verified_snapshot_closes_on_initialization_failure
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_structural_snapshot_lifetime
#   proves: structural_queries_keep_verified_snapshot
#   call: self::test_verified_snapshot_readonly_and_close
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_structural_evidence_canonical_bytes
#   proves: structural_complete_replay
#   call: self::test_resealed_noncanonical_evidence_is_rejected
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_structural_metadata_canonical_bytes
#   proves: structural_complete_replay
#   call: self::test_resealed_noncanonical_metadata_is_rejected
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_structural_glyph_axis_inventory
#   proves: structural_atomic_recovery
#   call: self::test_word_glyph_axes_follow_inventory
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_complete_raw_source_roundtrip
#   proves: structural_complete_raw_source
#   call: self::test_complete_raw_source_roundtrip
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_full_reduced_snapshot_requires_independent_raw_source
#   proves: structural_complete_raw_source
#   call: self::test_full_reduced_snapshot_requires_independent_raw_source
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_omitted_raw_fields_cannot_forge_complete_source
#   proves: structural_complete_raw_source
#   call: self::test_omitted_raw_fields_cannot_forge_complete_source
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_resealed_raw_source_corruption_refuses
#   proves: structural_complete_raw_source
#   call: self::test_resealed_raw_source_corruption_refuses
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_partial_artifact_rejects_raw_rows_and_claims
#   proves: structural_complete_raw_source
#   call: self::test_partial_artifact_rejects_raw_rows_and_claims
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_raw_source_symlinks_refuse
#   proves: structural_complete_raw_source
#   call: self::test_raw_source_symlinks_refuse
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_raw_source_preflight_rejects_oversize_before_read
#   proves: structural_complete_raw_source
#   call: self::test_raw_source_preflight_rejects_oversize_before_read
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_raw_payload_preflight_precedes_json_fetch_and_receipt
#   proves: structural_complete_raw_source
#   call: self::test_raw_payload_preflight_precedes_json_fetch_and_receipt
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_raw_tree_does_not_authorize_changed_projection
#   proves: structural_complete_raw_source
#   call: self::test_raw_tree_does_not_authorize_changed_projection
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_right_guillemet_retains_terminal_closure
#   proves: structural_local_closure
#   call: self::test_right_guillemet_retains_terminal_closure
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_raw_source_builder_requires_exact_file_count
#   proves: structural_complete_raw_source
#   call: self::test_raw_source_builder_requires_exact_file_count
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_raw_source_growth_after_preflight_is_bounded
#   proves: structural_complete_raw_source
#   call: self::test_raw_source_growth_after_preflight_is_bounded
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_embedded_replay_descriptor_independence
#   proves: structural_complete_raw_source
#   call: self::test_embedded_replay_does_not_require_filesystem_descriptor_support
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_raw_source_directory_traversal_is_bounded
#   proves: structural_complete_raw_source
#   call: self::test_raw_source_directory_traversal_is_bounded
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_raw_source_fifo_swap_refuses_without_blocking
#   proves: structural_complete_raw_source
#   call: self::test_raw_source_fifo_swap_refuses_without_blocking
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_complete_builder_rejects_float_source_count
#   proves: structural_complete_raw_source, structural_complete_replay
#   call: self::test_complete_builder_rejects_float_source_count
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_resealed_complete_source_rejects_float_counts
#   proves: structural_complete_raw_source, structural_complete_replay
#   call: self::test_resealed_complete_source_rejects_float_counts
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_manifest_requires_exact_json_types_against_database
#   proves: structural_complete_raw_source, structural_complete_replay
#   call: self::test_manifest_requires_exact_json_types_against_database
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_manifest_raw_bytes_must_be_canonical
#   proves: structural_complete_replay
#   call: self::test_manifest_raw_bytes_must_be_canonical
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_fresh_process_import_closure_is_fully_bound
#   proves: structural_complete_replay
#   call: self::test_fresh_process_import_closure_is_fully_bound
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# id: check_import_time_dependency_mutation_invalidates_implementation
#   proves: structural_complete_replay
#   call: self::test_import_time_dependency_mutation_invalidates_implementation
#   mutates: filesystem
#   cleanup: pytest_tmp_path
# === END CHECKS ===


def snapshot():
    return WordnetSnapshot(
        lexemes=(LexemeRecord("geometry", "n", (), (SenseRecord("s1", "n1", ()), SenseRecord("s2", "n2", ()))),
                 LexemeRecord("ice cream", "n", (), (SenseRecord("s3", "n3", ()),)),
                 LexemeRecord("Dr.", "n", (), (SenseRecord("s4", "n4", ()),))),
        synsets=(SynsetRecord("n1", "n", ("geometry",), ("Dr. creates geometry. Dr. creates 3.14...",), ()),
                 SynsetRecord("n2", "n", ("geometry",), ("geometry  geometry\ngeometry…",), ()),
                 SynsetRecord("n3", "n", ("ice cream",), ("ice cream",), ()),
                 SynsetRecord("n4", "n", ("Dr.",), ("Dr.",), ())),
        source_tree_sha256="0" * 64, source_file_count=4)


def make(path):
    return build(snapshot(), out_dir=path, public_position=lambda c: None,
                 producer={"standing": "fixture-only"})


@pytest.fixture
def field(tmp_path):
    path = tmp_path / "field"
    make(path)
    with StructuralField(path) as field:
        yield field


def test_exact_scalar_recovery():
    for text in ("", "  ", "geometry", "Dr.", "3.14", "...", "…", "a\r\nb", "can't", "x-ray", "e\u0301", "a.b", ".."):
        parts = segment(text)
        assert "".join(p.text for p in parts) == text
        assert [(p.start, p.end) for p in parts] == [(sum(len(q.text) for q in parts[:i]), sum(len(q.text) for q in parts[:i+1])) for i in range(len(parts))]
        assert all("." not in p.text and not any(c.isspace() for c in p.text) for p in parts if p.kind == "word")
    with pytest.raises(ValueError, match="scalars"):
        segment("\ud800")


def test_repetition_and_atomic_promotion(field):
    word = field.word("geometry")
    assert len(word["glyph_axis_set"]) == 7
    assert word["occurrence_count"] == 8
    assert word["glyph_ids"][1] == word["glyph_ids"][4]
    query = field.construct("creates creates")
    first, second = query["parts"][0], query["parts"][2]
    assert first["identity"] == second["identity"]
    assert first["start"] != second["start"]
    assert first["origin"] == second["origin"] == "O_W"
    composite = field.compose(query, relation="ordered-text")
    assert composite["standing"] == "logically-closed"
    assert composite["participants"][0] == composite["participants"][2]
    assert "glyph_ids" not in composite["participants"][0]
    assert field.word("geometry") == word


def test_period_roles_and_ambiguity(field):
    query = field.construct("Dr. creates 3.14...")
    roles = [(p["start"], p["function"]["roles"]) for p in query["parts"]]
    assert roles[1][1] == ["abbreviation"]
    assert any(r == ["decimal-separator"] for _, r in roles)
    assert sum("ellipsis" in r for _, r in roles) == 3
    terminal = field.construct("Dr.")
    assert terminal["input_closed"] is True
    assert terminal["logical_state"] == "closed"
    assert terminal["closure"] == [{"part": 1, "state": "hmmm"}]
    assert field.compose(terminal, relation="sentence")["code"] == "SENTENCE_CLOSURE_UNRESOLVED"
    explicit = field.construct("Dr.", boundary_decisions={"2": {"closed": True, "source": "operator:sentence-end"}})
    assert explicit["parts"][1]["function"]["roles"] == ["abbreviation", "sentence-close"]
    assert field.compose(explicit, relation="sentence")["standing"] == "logically-closed"
    assert field.replay(json.loads(canonical(explicit))) == explicit


@pytest.mark.parametrize("decisions", [{"0": {"closed": True, "source": "x"}}, {"2": {"closed": True, "source": ""}}, {"2": {"closed": 1, "source": "x"}}, {"9": {}}, {2: {"closed": True, "source": "x"}}])
def test_bad_decisions_refuse(field, decisions):
    with pytest.raises(StructuralError):
        field.construct("Dr.", boundary_decisions=decisions)


def test_ellipsis_distinction_and_group_decision(field):
    dots = field.construct("...")
    scalar = field.construct("…")
    assert len(dots["parts"]) == 3 and len(scalar["parts"]) == 1
    assert dots["receipt_sha256"] != scalar["receipt_sha256"]
    with pytest.raises(StructuralError, match="final scalar"):
        field.construct("...", boundary_decisions={"0": {"closed": True, "source": "x"}})


def test_ellipsis_explicit_closure(field):
    q = field.construct("geometry...", boundary_decisions={"10": {"closed": True, "source": "operator:end"}})
    assert q["closure"] == [{"part": 3, "state": "closed"}]
    assert field.compose(q, relation="sentence")["standing"] == "logically-closed"


def test_spaces_open_sites_without_empty_words(field):
    query = field.construct("geometry  geometry ")
    assert [s["event"] for s in query["word_sites"]] == ["open-site", "continue-site", "open-site"]
    assert query["next_word_site_open"] is True
    assert sum(p["kind"] == "word" for p in query["parts"]) == 2
    assert not field.construct("   ")["refusals"]
    assert field.compose(field.construct(""), relation="ordered-text")["standing"] == "refused"


def test_admission_and_geometry_refusals(field):
    before = field.db.total_changes
    query = field.construct("Geometry zzzz 🦄")
    assert len(query["refusals"]) == 3
    assert query["source"] == "Geometry zzzz 🦄"
    assert query["parts"][0]["identity"] is None
    assert field.db.total_changes == before
    assert field.compose(query, relation="ordered-text")["code"] == "PARTICIPANT_ADMISSION_REQUIRED"
    known = field.construct("geometry")
    assert field.compose(known, relation="acronym-promotion")["code"] == "RELATION_NOT_REGISTERED"
    assert field.geometry(known, operation="displacement")["edges"] == []
    assert field.geometry(known, operation="displacement")["code"] == "UCNS_OPERATION_REQUIRED"


def test_definition_topologies_and_origins(field):
    ids = [r[0] for r in field.db.execute("SELECT id FROM records WHERE kind='definition' ORDER BY id")]
    first, second = [field.definition(i) for i in ids[:2]]
    assert first["origin"] == second["origin"] == {"space": "O_D", "word_id": field.words["geometry"]}
    assert second["definition_succession"]["previous"] == ids[0]
    assert first["constituent_chain"] == [[n-1, n] for n in range(1, len(first["parts"]))]
    assert len(first["constituent_direct"]) == len(first["parts"])
    compound = field.definition(ids[2])
    abbreviation = field.definition(ids[3])
    assert compound["origin"] is None and abbreviation["origin"] is None
    assert compound["origin_state"] == "hmmm:compound-lexical-origin"
    assert "ice cream" not in field.words and "Dr." not in field.words
    assert field.word("geometry")["attachment"]["attachment_point_q_w"] == field.words["geometry"]


def test_query_tamper_detected(field):
    query = field.construct("geometry geometry")
    query["parts"][2]["identity"] += 1
    with pytest.raises(StructuralError, match="replay mismatch"):
        field.replay(query)


def test_complete_rebuild_and_tamper(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    first, second = make(a), make(b)
    assert first == second
    assert (a / "construct.db").read_bytes() == (b / "construct.db").read_bytes()
    assert verify(a) == first
    with sqlite3.connect(a / "construct.db") as db:
        db.execute("UPDATE words SET surface='changed' WHERE surface='geometry'")
    with pytest.raises(StructuralError, match="receipt"):
        verify(a)


@pytest.mark.parametrize("sql", ["DELETE FROM records WHERE id=(SELECT MAX(id) FROM records)",
    "UPDATE records SET provenance='{}' WHERE kind='definition'", "UPDATE components SET function='{}' WHERE record_id=1",
    "UPDATE word_characters SET character_id=1 WHERE ordinal=1"])
def test_resealed_structural_corruption_detected(tmp_path, sql):
    root = tmp_path / "state"
    make(root)
    with sqlite3.connect(root / "construct.db") as db:
        db.execute(sql)
        db.commit()
        manifest = _manifest(db)
    (root / "manifest.json").write_bytes(canonical(manifest) + b"\n")
    with pytest.raises(StructuralError):
        verify(root)


def test_failed_build_publishes_no_partial_state(tmp_path):
    source = snapshot()
    bad = replace(source, synsets=())
    root = tmp_path / "bad"
    with pytest.raises(StructuralError, match="missing synset"):
        build(bad, out_dir=root, public_position=lambda c: None, producer={"standing": "fixture"})
    assert not root.exists()
    assert not list(tmp_path.glob('.structural-*'))


def reseal(root, change):
    """Adversarial helper: row receipts alone must not authorize source claims."""
    with sqlite3.connect(root / "construct.db") as db:
        change(db)
        db.commit()
        manifest = _manifest(db)
    (root / "manifest.json").write_bytes(canonical(manifest) + b"\n")


def test_caller_cannot_grant_complete_corpus(tmp_path):
    root = tmp_path / "state"
    with pytest.raises(StructuralError, match="exact pinned source"):
        build(snapshot(), out_dir=root, public_position=lambda c: None,
              producer={"standing": "fixture"}, complete_corpus=True)
    assert not root.exists()


@pytest.mark.parametrize("value", [1, "true", None, [], {}])
def test_completeness_requires_boolean(tmp_path, value):
    with pytest.raises(StructuralError, match="boolean"):
        build(snapshot(), out_dir=tmp_path / "state", public_position=lambda c: None,
              producer={}, complete_corpus=value)


@pytest.mark.parametrize("key,value", [
    ("authority_transfer", True), ("authority_transfer", 0),
    ("geometry_state", "executed"), ("normalization", "NFC"),
    ("definition_topologies", ["constituent-direct"]),
    ("complete_corpus", True), ("complete_corpus", 0),
    ("extra_authority", "graduated"),
])
def test_resealed_metadata_boundary_refuses(tmp_path, key, value):
    root = tmp_path / "state"
    make(root)
    reseal(root, lambda db: db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (key, canonical(value).decode("utf-8"))))
    with pytest.raises(StructuralError):
        verify(root)


def test_resealed_pinned_source_claim_requires_all_evidence(tmp_path):
    from english_gonol.structural_construct import PINNED_SOURCE
    root = tmp_path / "state"
    make(root)
    def change(db):
        db.execute("UPDATE meta SET value=? WHERE key='source'", (canonical(PINNED_SOURCE).decode("utf-8"),))
        db.execute("UPDATE meta SET value='true' WHERE key='complete_corpus'")
    reseal(root, change)
    with pytest.raises(StructuralError, match="raw source file count"):
        verify(root)


@pytest.mark.parametrize("kind,field,value", [
    ("lexeme", "part_of_speech", "forged"),
    ("synset", "relations", [["invented", ["n1"]]]),
    ("synset", "part_of_speech", "forged"),
])
def test_unused_included_source_evidence_cannot_be_resealed(tmp_path, kind, field, value):
    root = tmp_path / "state"
    make(root)
    def change(db):
        payload = json.loads(db.execute("SELECT payload FROM evidence WHERE kind=? AND ordinal=0", (kind,)).fetchone()[0])
        payload[field] = value
        db.execute("UPDATE evidence SET payload=? WHERE kind=? AND ordinal=0", (canonical(payload).decode("utf-8"), kind))
    reseal(root, change)
    with pytest.raises(StructuralError, match="source evidence digest"):
        verify(root)


@pytest.fixture
def punctuation_field(tmp_path):
    source = snapshot()
    source = replace(source, synsets=source.synsets + (
        SynsetRecord("punctuation", "n", ("geometry",), ('"geometry." (geometry!?) [geometry.] {geometry!} “geometry?” geometry; geometry, «geometry.»', "'geometry.'"), ()),))
    root = tmp_path / "punctuation"
    build(source, out_dir=root, public_position=lambda c: None, producer={"standing": "fixture"})
    with StructuralField(root) as result:
        yield result


@pytest.mark.parametrize("text", ['"geometry."', '(geometry!?)', '[geometry.]', '{geometry!}',
                                   '“geometry?”', 'geometry!?', 'geometry?!', 'geometry!!',
                                   '"geometry!?"  '])
def test_terminal_closing_punctuation_and_clusters(punctuation_field, text):
    query = punctuation_field.construct(text)
    assert not query["refusals"]
    result = punctuation_field.compose(query, relation="sentence")
    assert result["standing"] == "logically-closed"
    assert len(result["participants"]) == len(query["parts"])
    assert punctuation_field.replay(query) == query


@pytest.mark.parametrize("text", ['geometry. geometry.', 'geometry! ?', 'geometry.;',
                                   'geometry.,', 'geometry...', 'Dr.', 'geometry'])
def test_nonterminal_or_ambiguous_closure_still_refuses(punctuation_field, text):
    query = punctuation_field.construct(text)
    assert not query["refusals"]
    assert punctuation_field.compose(query, relation="sentence")["code"] == "SENTENCE_CLOSURE_UNRESOLVED"


def test_explicit_open_ambiguity_is_a_resolved_nonboundary(field):
    text = "Dr. creates geometry."
    query = field.construct(text, boundary_decisions={
        "2": {"closed": False, "source": "operator:abbreviation-not-sentence-end"}})
    assert query["closure"][0]["state"] == "open"
    assert field.compose(query, relation="sentence")["standing"] == "logically-closed"
    assert field.replay(query) == query
    undecided = field.construct(text)
    assert field.compose(undecided, relation="sentence")["code"] == "SENTENCE_CLOSURE_UNRESOLVED"
    nonterminal = field.construct(text, boundary_decisions={
        "2": {"closed": True, "source": "operator:independent-boundary"}})
    assert field.compose(nonterminal, relation="sentence")["code"] == "SENTENCE_CLOSURE_UNRESOLVED"


@pytest.mark.parametrize("sql", [
    "ALTER TABLE characters ADD COLUMN extra TEXT",
    "ALTER TABLE words ADD COLUMN extra TEXT",
    "DROP INDEX components_word",
    "CREATE VIEW extra AS SELECT * FROM words",
    "CREATE VIEW sqliteXextra AS SELECT * FROM words",
    "CREATE TRIGGER sqliteXextra AFTER INSERT ON words BEGIN SELECT 1; END",
    "CREATE TRIGGER extra AFTER INSERT ON words BEGIN SELECT 1; END",
])
def test_resealed_schema_tamper_refuses_before_query(tmp_path, sql):
    root = tmp_path / "state"
    make(root)
    reseal(root, lambda db: db.execute(sql))
    with pytest.raises(StructuralError, match="schema"):
        verify(root)
    with pytest.raises(StructuralError, match="schema"):
        StructuralField(root)


def test_manifest_edits_do_not_redefine_verified_field(field):
    original = field.construct("Dr.")
    exposed = field.manifest
    exposed["receipt_sha256"] = "forged"
    exposed["metadata"]["profile_sha256"] = "forged"
    exposed["metadata"]["profile"]["abbreviations"].remove("Dr")
    assert field.construct("Dr.") == original
    assert field.replay(original) == original
    assert field.manifest != exposed
    with pytest.raises(AttributeError):
        field.manifest = exposed
    with pytest.raises(AttributeError):
        field.abbreviations = ()
    with pytest.raises(AttributeError):
        field.abbreviations.remove("Dr")


def test_implementation_inputs_are_the_full_forge_check_surface():
    from english_gonol.structural_construct import IMPLEMENTATION_FILES
    assert set(IMPLEMENTATION_FILES) == {
        "structural_rules.py", "structural_construct.py", "structural_query.py",
        "hyperspace_construct.py", "full_construct_run.py", "language/source.py",
        "language/__init__.py", "language/affixes.py", "language/manifest.py",
        "language/model.py", "language/morphology.py", "language/relational_bridge.py",
        "language/rendering.py"}


@pytest.mark.parametrize("text", ["'geometry.'", "'geometry!?'", "'geometry.'  "])
def test_ascii_single_quote_is_a_terminal_closer(punctuation_field, text):
    query = punctuation_field.construct(text)
    assert not query["refusals"]
    assert punctuation_field.compose(query, relation="sentence")["standing"] == "logically-closed"
    assert punctuation_field.replay(query) == query


@pytest.mark.parametrize("operation", ["update", "replace"])
@pytest.mark.parametrize("timing", ["before-first-query", "after-first-query"])
def test_external_changes_cannot_replace_verified_query_rows(tmp_path, monkeypatch, operation, timing):
    from english_gonol import structural_query
    root = tmp_path / "state"
    make(root)
    path = root / "construct.db"
    replacement = tmp_path / "replacement.db"
    replacement.write_bytes(path.read_bytes())
    with StructuralField(root) as original:
        expected_word = original.word("geometry")
        rid = original.db.execute("SELECT MIN(id) FROM records WHERE kind='definition'").fetchone()[0]
        expected_definition = original.definition(rid)
        expected_query = original.construct("geometry")
        expected_manifest = original.manifest
    mutations = []

    def mutate():
        target = path if operation == "update" else replacement
        with closing(sqlite3.connect(target, timeout=0)) as db:
            db.execute("UPDATE words SET surface='forged' WHERE surface='geometry'")
            db.execute("UPDATE records SET text='forged' WHERE kind='definition'")
            if operation == "update":
                # The verified read snapshot holds its lock; in-place writers cannot commit.
                with pytest.raises(sqlite3.OperationalError, match="locked"):
                    db.commit()
                db.rollback()
            else:
                db.commit()
        if operation == "replace":
            replacement.replace(path)
        mutations.append(operation)

    original_canonical = structural_query.canonical
    def mutate_after_verification(value):
        if timing == "before-first-query" and not mutations:
            mutate()
        return original_canonical(value)
    monkeypatch.setattr(structural_query, "canonical", mutate_after_verification)
    with StructuralField(root) as field:
        if timing == "after-first-query":
            assert field.word("geometry") == expected_word
            assert field.definition(rid) == expected_definition
            mutate()
        assert mutations == [operation]
        assert field.word("geometry") == expected_word
        assert field.definition(rid) == expected_definition
        assert field.construct("geometry") == expected_query
        assert field.manifest == expected_manifest
        assert "forged" not in field.words
    if operation == "replace":
        with pytest.raises(StructuralError, match="receipt"):
            verify(root)
    else:
        assert verify(root) == expected_manifest


@pytest.mark.parametrize("stage", ["verification", "initialization"])
def test_verified_snapshot_closes_on_initialization_failure(tmp_path, monkeypatch, stage):
    from english_gonol import structural_construct, structural_query
    root = tmp_path / "state"
    make(root)
    connections = []
    original_open = structural_construct.open_readonly
    def track_open(path):
        db = original_open(path)
        connections.append(db)
        return db
    monkeypatch.setattr(structural_construct, "open_readonly", track_open)
    if stage == "verification":
        manifest = json.loads((root / "manifest.json").read_bytes())
        manifest["receipt_sha256"] = "forged"
        (root / "manifest.json").write_bytes(canonical(manifest) + b"\n")
    else:
        def refuse_inventory(_db):
            raise StructuralError("inventory failure")
        monkeypatch.setattr(structural_query, "glyph_inventory", refuse_inventory)
    with pytest.raises(StructuralError):
        StructuralField(root)
    assert len(connections) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connections[0].execute("SELECT 1")


def test_verified_snapshot_readonly_and_close(tmp_path):
    root = tmp_path / "state"
    make(root)
    with StructuralField(root) as field:
        assert field.db.in_transaction
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            field.db.execute("UPDATE words SET surface='forged'")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        field.db.execute("SELECT 1")
    field.close()
    with pytest.raises(RuntimeError, match="caller failure"):
        with StructuralField(root) as field:
            raise RuntimeError("caller failure")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        field.db.execute("SELECT 1")


@pytest.mark.parametrize("kind", ["lexeme", "synset"])
@pytest.mark.parametrize("variant", ["pretty", "escape", "duplicate-key"])
def test_resealed_noncanonical_evidence_is_rejected(tmp_path, kind, variant):
    root = tmp_path / "state"
    make(root)
    def change(db):
        raw = db.execute("SELECT payload FROM evidence WHERE kind=? AND ordinal=0", (kind,)).fetchone()[0]
        item = json.loads(raw)
        if variant == "pretty":
            mutated = json.dumps(item, ensure_ascii=False, indent=2, sort_keys=True)
        elif variant == "escape":
            mutated = raw.replace("geometry", "\\u0067eometry")
        else:
            key = next(iter(item))
            mutated = "{" + canonical(key).decode() + ":" + canonical(item[key]).decode() + "," + raw[1:]
        assert mutated != raw and json.loads(mutated) == item
        db.execute("UPDATE evidence SET payload=? WHERE kind=? AND ordinal=0", (mutated, kind))
    reseal(root, change)
    with pytest.raises(StructuralError, match="noncanonical source evidence"):
        verify(root)
    with pytest.raises(StructuralError, match="noncanonical source evidence"):
        StructuralField(root)


def test_word_glyph_axes_follow_inventory(tmp_path):
    root = tmp_path / "state"
    make(root)
    with StructuralField(root) as field:
        word = field.word("geometry")
        inventory = glyph_inventory(field.db)
        assert word["glyph_axis_set"] == sorted({inventory[c].axis_index for c in "geometry"})
        assert word["glyph_axis_set"] != sorted(set(word["glyph_ids"]))
        assert word["glyph_axis_set"] == sorted({gid - 1 for gid in word["glyph_ids"]})
        assert word["occurrence_count"] == 8
        assert word["glyph_ids"][1] == word["glyph_ids"][4]
        assert word["glyph_origin"] == "O_G"
        assert word["gonal_order"] == "hmmm:UCNS_OPERATION_REQUIRED"


def test_verified_carrier_glyph_axes_follow_inventory(tmp_path, pinned_raw_source):
    root = raw_field(tmp_path, pinned_raw_source)
    carrier = pinned_raw_source[2]["producer"]["carrier"]
    with StructuralField(root) as field:
        word = field.word("geometry")
        inventory = glyph_inventory(field.db)
        assert word["glyph_axis_set"] == sorted({inventory[c].axis_index for c in "geometry"})
        assert all(field.characters[c][1] == carrier.index(c) for c in "geometry")


@pytest.mark.parametrize("positions", [{"g": 0}, {c: 0 for c in "geometry"}])
def test_partial_build_refuses_unverified_carrier_positions(tmp_path, positions):
    root = tmp_path / "state"
    with pytest.raises(StructuralError, match="partial build refuses carrier positions before writing"):
        build(snapshot(), out_dir=root, public_position=positions.get, producer={"standing": "fixture-only"})
    assert not root.exists()
    assert not list(tmp_path.glob(".structural-*"))


def test_partial_build_records_no_source_commit(tmp_path):
    root = tmp_path / "state"
    manifest = make(root)
    assert manifest["metadata"]["source"]["commit"] is None
    from english_gonol.structural_construct import OEWN_COMMIT
    reseal(root, lambda db: db.execute("UPDATE meta SET value=? WHERE key='source'", (
        canonical({**manifest["metadata"]["source"], "commit": OEWN_COMMIT}).decode(),)))
    with pytest.raises(StructuralError, match="pinned source completeness"):
        verify(root)


def test_complete_build_claims_pinned_source_commit(tmp_path, pinned_raw_source):
    from english_gonol.structural_construct import OEWN_COMMIT
    root = raw_field(tmp_path, pinned_raw_source)
    assert verify(root)["metadata"]["source"]["commit"] == OEWN_COMMIT
    with StructuralField(root) as field:
        assert field.complete_corpus is True


def test_partial_field_reports_complete_corpus_false(tmp_path):
    root = tmp_path / "state"
    make(root)
    with StructuralField(root) as field:
        assert field.complete_corpus is False
        with pytest.raises(AttributeError):
            field.complete_corpus = True


@pytest.mark.parametrize("kind", ["symlink", "directory"])
def test_nonregular_database_refuses(tmp_path, kind):
    root = tmp_path / "state"
    make(root)
    db = root / "construct.db"
    if kind == "symlink":
        outside = tmp_path / "outside.db"
        db.rename(outside)
        db.symlink_to(outside)
    else:
        db.unlink()
        db.mkdir()
    with pytest.raises(StructuralError, match="regular"):
        verify(root)
    with pytest.raises(StructuralError, match="regular"):
        StructuralField(root)


@pytest.mark.parametrize("sql", ["UPDATE characters SET public_position=0 WHERE scalar='g'",
                                 "UPDATE characters SET public_position=id"])
def test_resealed_partial_carrier_positions_refuse(tmp_path, sql):
    root = tmp_path / "state"
    make(root)
    reseal(root, lambda db: db.execute(sql))
    with pytest.raises(StructuralError, match="unverified carrier positions"):
        verify(root)
    with pytest.raises(StructuralError, match="unverified carrier positions"):
        StructuralField(root)


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
def test_sqlite_sidecar_files_refuse(tmp_path, suffix):
    root = tmp_path / "state"
    make(root)
    verify(root)
    (root / ("construct.db" + suffix)).write_bytes(b"")
    with pytest.raises(StructuralError, match="sidecar"):
        verify(root)
    with pytest.raises(StructuralError, match="sidecar"):
        StructuralField(root)


def test_resealed_wal_state_refuses(tmp_path):
    root = tmp_path / "state"
    make(root)
    db = sqlite3.connect(root / "construct.db")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA wal_autocheckpoint=0")
    db.execute("UPDATE words SET surface=surface WHERE id=1")
    db.commit()
    (root / "manifest.json").write_bytes(canonical(_manifest(db)) + b"\n")
    assert (root / "construct.db-wal").exists()
    with pytest.raises(StructuralError, match="sidecar|WAL"):
        verify(root)
    db.close()
    for suffix in ("-wal", "-shm"):
        (root / ("construct.db" + suffix)).unlink(missing_ok=True)
    with pytest.raises(StructuralError, match="WAL"):
        verify(root)


@pytest.mark.parametrize("variant", ["pretty", "escape", "duplicate-key"])
def test_resealed_noncanonical_metadata_is_rejected(tmp_path, variant):
    root = tmp_path / "state"
    make(root)
    def change(db):
        raw = db.execute("SELECT value FROM meta WHERE key='producer'").fetchone()[0]
        item = json.loads(raw)
        if variant == "pretty":
            mutated = json.dumps(item, ensure_ascii=False, indent=2, sort_keys=True)
        elif variant == "escape":
            mutated = raw.replace("fixture", "\\u0066ixture")
        else:
            mutated = '{"standing":"fixture-only",' + raw[1:]
        assert mutated != raw and json.loads(mutated) == item
        db.execute("UPDATE meta SET value=? WHERE key='producer'", (mutated,))
    reseal(root, change)
    with pytest.raises(StructuralError, match="noncanonical metadata"):
        verify(root)
    with pytest.raises(StructuralError, match="noncanonical metadata"):
        StructuralField(root)


@pytest.fixture
def pinned_raw_source(tmp_path, monkeypatch):
    from english_gonol import structural_construct as module
    from english_gonol.language import source as loader
    from english_gonol.language.source import load_oewn_2025
    monkeypatch.setattr(loader, "OEWN_EXPECTED_WORD_COUNT", 1)
    monkeypatch.setattr(loader, "OEWN_EXPECTED_SYNSET_COUNT", 1)
    root = tmp_path / "yaml"
    root.mkdir()
    (root / "frames.yaml").write_text("{}\n")
    (root / "entries-g.yaml").write_text(
        "geometry:\n  n:\n    pronunciation: [original]\n    sense:\n      - id: s1\n        synset: n1\n")
    (root / "noun.yaml").write_text(
        "n1:\n  partOfSpeech: n\n  members: [geometry]\n  definition: [geometry.]\n"
        "  example: [original]\n  source: original\n  wikidata: Q1\n")
    source = load_oewn_2025(root)
    identity = {**module.PINNED_SOURCE, "tree_sha256": source.source_tree_sha256,
                "files": source.source_file_count, "lexemes": len(source.lexemes),
                "synsets": len(source.synsets), "evidence_sha256": module._evidence_digest(
                    (kind, i, asdict(item))
                    for kind, items in (("lexeme", source.lexemes), ("synset", source.synsets))
                    for i, item in enumerate(items))}
    monkeypatch.setattr(module, "PINNED_SOURCE", identity)
    # Verbatim carrier order from UCNS's pinned public_gonol.py, checked by its digest.
    carrier = list(' A!"B#$C%(D&\'E1*F+[G,-H./I3{J:;K=?L<@M5\\N^_O‘`P|~Q7…R“—S–·T°«U9±V×÷W√∂X∫∑Y∏∇Z∞≈≠a≤≥b→←c)↑d↓2e↔⊕f]⊗g⊙⊘h∈4i}∉j⊂⊃k⊆>l⊇6m∩∪n∧’o∨¬p∀8q∃”r⊢⊨s∴∵t»0u≡ψvφωwαβxγδyλπzσ')
    assert digest(carrier) == module.PUBLIC_GONOL_SHA256
    producer = {"repository": "The-Interdependency/ucns", "commit": module.UCNS_PUBLIC_GONOL_COMMIT,
                "module_sha256": module.UCNS_PUBLIC_GONOL_MODULE_SHA256,
                "carrier_sha256": module.PUBLIC_GONOL_SHA256, "carrier": carrier}
    positions = {c: i for i, c in enumerate(carrier)}
    return root, source, {"public_position": positions.get, "producer": producer}


def partial(options):
    """Partial fields carry no carrier positions; only complete fields bind UCNS order."""
    return {**options, "public_position": lambda c: None}


def raw_field(tmp_path, pinned_raw_source):
    root, source, options = pinned_raw_source
    output = tmp_path / "raw-field"
    build(source, out_dir=output, source_root=root, complete_corpus=True, **options)
    return output


def test_complete_raw_source_roundtrip(tmp_path, pinned_raw_source):
    from english_gonol.language.source import _source_tree_digest
    source_root, source, options = pinned_raw_source
    root = raw_field(tmp_path, pinned_raw_source)
    manifest = verify(root)
    assert manifest["version"] == "1.1.0"
    assert manifest["metadata"]["complete_corpus"] is True
    assert manifest["counts"]["evidence"] == len(source.lexemes) + len(source.synsets) + source.source_file_count
    recovered = tmp_path / "recovered"
    recovered.mkdir()
    with closing(sqlite3.connect(root / "construct.db")) as db:
        rows = db.execute("SELECT ordinal,payload FROM evidence WHERE kind='source-file' ORDER BY ordinal").fetchall()
    assert [i for i, _ in rows] == list(range(source.source_file_count))
    for _, payload in rows:
        item = json.loads(payload)
        assert canonical(item).decode() == payload
        data = base64.b64decode(item["base64"], validate=True)
        assert data == (source_root / item["path"]).read_bytes()
        (recovered / item["path"]).write_bytes(data)
    assert _source_tree_digest(recovered.rglob("*.yaml"), recovered) == source.source_tree_sha256
    second = tmp_path / "second"
    assert build(source, out_dir=second, source_root=source_root, complete_corpus=True, **options) == manifest
    assert (second / "construct.db").read_bytes() == (root / "construct.db").read_bytes()
    with StructuralField(root) as field:
        assert not field.construct("geometry.")["refusals"]


@pytest.mark.parametrize("complete", [False, True])
def test_full_reduced_snapshot_requires_independent_raw_source(tmp_path, pinned_raw_source, complete):
    _root, source, options = pinned_raw_source
    output = tmp_path / "snapshot-only"
    if complete:
        with pytest.raises(StructuralError, match="independent raw source"):
            build(source, out_dir=output, complete_corpus=True, **options)
        assert not output.exists()
    else:
        manifest = build(source, out_dir=output, **partial(options))
        assert manifest["metadata"]["complete_corpus"] is False
        assert verify(output) == manifest
        assert manifest["counts"]["evidence"] == len(source.lexemes) + len(source.synsets)
        reseal(output, lambda db: db.execute("UPDATE meta SET value='true' WHERE key='complete_corpus'"))
        with pytest.raises(StructuralError, match="pinned source completeness"):
            verify(output)


@pytest.mark.parametrize("field", ["pronunciation", "example", "source", "wikidata"])
def test_omitted_raw_fields_cannot_forge_complete_source(tmp_path, pinned_raw_source, field):
    from english_gonol.language.source import load_oewn_2025
    root, original, options = pinned_raw_source
    path = root / ("entries-g.yaml" if field == "pronunciation" else "noun.yaml")
    text = path.read_text()
    value = "Q1" if field == "wikidata" else "[original]" if field in {"pronunciation", "example"} else "original"
    text = text.replace(f"{field}: {value}", f"{field}: changed")
    path.write_text(text)
    changed = load_oewn_2025(root)
    assert changed.lexemes == original.lexemes and changed.synsets == original.synsets
    assert changed.source_tree_sha256 != original.source_tree_sha256
    forged = replace(changed, source_tree_sha256=original.source_tree_sha256)
    output = tmp_path / "forged"
    with pytest.raises(StructuralError, match="raw source tree digest"):
        build(forged, out_dir=output, complete_corpus=True, source_root=root, **options)
    assert not output.exists() and not list(tmp_path.glob(".structural-*"))


@pytest.mark.parametrize("variant", [
    "altered", "missing", "extra", "duplicate-path", "reordered", "ordinal-gap",
    "parent-path", "absolute-path", "noncanonical-path", "backslash-path",
    "pretty-json", "escaped-json", "duplicate-json-key", "base64-whitespace", "base64-padding",
    "base64-invalid", "base64-type", "extra-field", "nonobject",
])
def test_resealed_raw_source_corruption_refuses(tmp_path, pinned_raw_source, variant):
    root = raw_field(tmp_path, pinned_raw_source)
    def change(db):
        rows = db.execute("SELECT ordinal,payload FROM evidence WHERE kind='source-file' ORDER BY ordinal").fetchall()
        ordinal, raw = rows[0]
        item = json.loads(raw)
        if variant == "missing":
            db.execute("DELETE FROM evidence WHERE kind='source-file' AND ordinal=0")
            return
        if variant == "extra":
            db.execute("INSERT INTO evidence VALUES('source-file',?,?)", (len(rows), raw))
            return
        if variant == "ordinal-gap":
            db.execute("UPDATE evidence SET ordinal=99 WHERE kind='source-file' AND ordinal=0")
            return
        if variant == "reordered":
            db.execute("UPDATE evidence SET payload=? WHERE kind='source-file' AND ordinal=1", (raw,))
            raw = rows[1][1]
        elif variant == "duplicate-path":
            item["path"] = json.loads(rows[1][1])["path"]
        elif variant == "altered":
            item["base64"] = base64.b64encode(base64.b64decode(item["base64"]) + b"# changed\n").decode()
        elif variant == "parent-path":
            item["path"] = "../entries-g.yaml"
        elif variant == "absolute-path":
            item["path"] = "/entries-g.yaml"
        elif variant == "noncanonical-path":
            item["path"] = "./entries-g.yaml"
        elif variant == "backslash-path":
            item["path"] = "..\\entries-g.yaml"
        elif variant == "pretty-json":
            raw = json.dumps(item, indent=2)
        elif variant == "escaped-json":
            raw = raw.replace("entries", "\\u0065ntries")
        elif variant == "duplicate-json-key":
            raw = '{"path":' + json.dumps(item["path"]) + "," + raw[1:]
        elif variant == "base64-whitespace":
            item["base64"] += "\n"
        elif variant == "base64-padding":
            # Nonzero unused pad bits decode successfully but are not canonical.
            item["base64"] = "Zh=="
            assert base64.b64decode(item["base64"], validate=True) == b"f"
        elif variant == "base64-invalid":
            item["base64"] = "!!!!"
        elif variant == "base64-type":
            item["base64"] = [1]
        elif variant == "extra-field":
            item["extra"] = True
        elif variant == "nonobject":
            item = []
        if variant not in {"reordered", "pretty-json", "escaped-json", "duplicate-json-key"}:
            raw = canonical(item).decode()
        db.execute("UPDATE evidence SET payload=? WHERE kind='source-file' AND ordinal=?", (raw, ordinal))
    reseal(root, change)
    with pytest.raises(StructuralError):
        verify(root)
    with pytest.raises(StructuralError):
        StructuralField(root)


def test_partial_artifact_rejects_raw_rows_and_claims(tmp_path, pinned_raw_source):
    source_root, source, options = pinned_raw_source
    with pytest.raises(StructuralError, match="explicit complete corpus"):
        build(source, out_dir=tmp_path / "ambiguous", source_root=source_root, **options)
    root = tmp_path / "partial"
    build(source, out_dir=root, **partial(options))
    reseal(root, lambda db: db.execute("INSERT INTO evidence VALUES('source-file',0,?)",
                                    (canonical({"path": "frames.yaml", "base64": "e30K"}).decode(),)))
    with pytest.raises(StructuralError, match="partial corpus"):
        verify(root)


@pytest.mark.parametrize("kind", ["file", "directory"])
def test_raw_source_symlinks_refuse(tmp_path, pinned_raw_source, kind):
    source_root, source, options = pinned_raw_source
    target = source_root / ("entries-g.yaml" if kind == "file" else "linked")
    if kind == "file":
        external = tmp_path / "external.yaml"
        target.rename(external)
        target.symlink_to(external)
    else:
        target.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(StructuralError, match="symlink"):
        build(source, out_dir=tmp_path / "linked-field", source_root=source_root, complete_corpus=True, **options)


def test_raw_source_preflight_rejects_oversize_before_read(tmp_path, monkeypatch, pinned_raw_source):
    from english_gonol import structural_construct as module
    source_root, source, options = pinned_raw_source
    with (source_root / "entries-g.yaml").open("wb") as stream:
        stream.truncate(module.RAW_SOURCE_MAX_FILE_BYTES + 1)
    def forbidden_read(*_args):
        raise AssertionError("oversized file must be rejected before reading")
    monkeypatch.setattr(module, "_read_raw_source", forbidden_read)
    with pytest.raises(StructuralError, match="resource limits"):
        build(source, out_dir=tmp_path / "oversized", source_root=source_root, complete_corpus=True, **options)


def test_raw_payload_preflight_precedes_json_fetch_and_receipt(tmp_path, monkeypatch, pinned_raw_source):
    from english_gonol import structural_construct as module
    root = raw_field(tmp_path, pinned_raw_source)
    with closing(sqlite3.connect(root / "construct.db")) as db:
        db.execute("UPDATE evidence SET payload=zeroblob(?) WHERE kind='source-file' AND ordinal=0",
                   (4 * ((module.RAW_SOURCE_MAX_FILE_BYTES + 2) // 3) + 1000,))
        db.commit()
    def forbidden_receipt(_db):
        raise AssertionError("oversized raw payload must be rejected before row receipt reads")
    monkeypatch.setattr(module, "_manifest", forbidden_receipt)
    with pytest.raises(StructuralError, match="payload exceeds pinned resource limits"):
        verify(root)


def test_raw_tree_does_not_authorize_changed_projection(tmp_path, pinned_raw_source):
    source_root, source, options = pinned_raw_source
    changed = replace(source, lexemes=(replace(source.lexemes[0], part_of_speech="forged"),))
    with pytest.raises(StructuralError, match="exact pinned source evidence"):
        build(changed, out_dir=tmp_path / "forged-projection", source_root=source_root,
              complete_corpus=True, **options)
    root = raw_field(tmp_path, pinned_raw_source)
    def change(db):
        item = json.loads(db.execute("SELECT payload FROM evidence WHERE kind='lexeme' AND ordinal=0").fetchone()[0])
        item["part_of_speech"] = "forged"
        db.execute("UPDATE evidence SET payload=? WHERE kind='lexeme' AND ordinal=0", (canonical(item).decode(),))
    reseal(root, change)
    with pytest.raises(StructuralError, match="source evidence digest"):
        verify(root)


def test_right_guillemet_retains_terminal_closure(punctuation_field):
    text = "«geometry.»"
    query = punctuation_field.construct(text)
    assert not query["refusals"]
    assert query["closure"] == [{"part": 2, "state": "closed"}]
    result = punctuation_field.compose(query, relation="sentence")
    assert result["standing"] == "logically-closed"
    assert len(result["participants"]) == 4
    assert punctuation_field.replay(query) == query


@pytest.mark.parametrize("change", ["missing", "extra"])
def test_raw_source_builder_requires_exact_file_count(tmp_path, pinned_raw_source, change):
    source_root, source, options = pinned_raw_source
    if change == "missing":
        (source_root / "frames.yaml").unlink()
    else:
        (source_root / "extra.yaml").write_text("{}\n")
    with pytest.raises(StructuralError, match="file count"):
        build(source, out_dir=tmp_path / "wrong-count", source_root=source_root,
              complete_corpus=True, **options)


def test_raw_source_growth_after_preflight_is_bounded(tmp_path, monkeypatch, pinned_raw_source):
    from english_gonol import structural_construct as module
    source_root, source, options = pinned_raw_source
    original_read = module._read_raw_source
    def grow_then_read(root, name, limit):
        with (root / name).open("wb") as stream:
            stream.truncate(limit + 1)
        return original_read(root, name, limit)
    monkeypatch.setattr(module, "_read_raw_source", grow_then_read)
    with pytest.raises(StructuralError, match="resource limits"):
        build(source, out_dir=tmp_path / "grown", source_root=source_root,
              complete_corpus=True, **options)
    assert not list(tmp_path.glob(".structural-*"))



def test_embedded_replay_does_not_require_filesystem_descriptor_support(tmp_path, monkeypatch, pinned_raw_source):
    from english_gonol import structural_construct as module
    root = raw_field(tmp_path, pinned_raw_source)
    expected = verify(root)
    source_root, source, options = pinned_raw_source
    monkeypatch.delattr(module.os, "O_NOFOLLOW")
    assert verify(root) == expected
    with StructuralField(root) as field:
        assert not field.construct("geometry.")["refusals"]
    with pytest.raises(StructuralError, match="no-follow directory descriptor support"):
        build(source, out_dir=tmp_path / "unsupported", source_root=source_root,
              complete_corpus=True, **options)
    assert build(source, out_dir=tmp_path / "partial-portable", **partial(options))["metadata"]["complete_corpus"] is False



@pytest.mark.parametrize("kind", ["non-yaml", "directory", "too-many"])
def test_raw_source_directory_traversal_is_bounded(tmp_path, pinned_raw_source, kind):
    from english_gonol import structural_construct as module
    source_root, source, options = pinned_raw_source
    if kind == "non-yaml":
        (source_root / "ignored.txt").write_text("must not be ignored")
    elif kind == "directory":
        (source_root / "subtree").mkdir()
        (source_root / "subtree" / "hidden.yaml").write_text("{}\n")
    else:
        for number in range(module.RAW_SOURCE_MAX_FILES):
            (source_root / f"extra-{number}.yaml").write_text("{}\n")
    with pytest.raises(StructuralError, match="flat regular YAML|resource limits"):
        build(source, out_dir=tmp_path / "unbounded", source_root=source_root,
              complete_corpus=True, **options)


def test_raw_source_fifo_swap_refuses_without_blocking(tmp_path, monkeypatch, pinned_raw_source):
    from english_gonol import structural_construct as module
    if not hasattr(module.os, "mkfifo"):
        pytest.skip("FIFO regression requires POSIX mkfifo")
    source_root, source, options = pinned_raw_source
    original_read, original_open = module._read_raw_source, module.os.open
    def swap_then_read(root, name, limit):
        target = root / name
        target.unlink()
        module.os.mkfifo(target)
        def guarded_open(path, flags, **kwargs):
            # Assert the safety flag before the system call so a regression cannot hang.
            if path == name:
                assert flags & module.os.O_NONBLOCK
            return original_open(path, flags, **kwargs)
        monkeypatch.setattr(module.os, "open", guarded_open)
        return original_read(root, name, limit)
    monkeypatch.setattr(module, "_read_raw_source", swap_then_read)
    with pytest.raises(StructuralError, match="descriptor must be a regular file"):
        build(source, out_dir=tmp_path / "fifo", source_root=source_root,
              complete_corpus=True, **options)
    assert not list(tmp_path.glob(".structural-*"))



def test_complete_builder_rejects_float_source_count(tmp_path, pinned_raw_source):
    source_root, source, options = pinned_raw_source
    forged = replace(source, source_file_count=float(source.source_file_count))
    with pytest.raises(StructuralError, match="exact pinned source evidence"):
        build(forged, out_dir=tmp_path / "float-source", source_root=source_root,
              complete_corpus=True, **options)


@pytest.mark.parametrize("key", ["files", "lexemes", "synsets"])
def test_resealed_complete_source_rejects_float_counts(tmp_path, pinned_raw_source, key):
    root = raw_field(tmp_path, pinned_raw_source)
    def change(db):
        source = json.loads(db.execute("SELECT value FROM meta WHERE key='source'").fetchone()[0])
        source[key] = float(source[key])
        db.execute("UPDATE meta SET value=? WHERE key='source'", (canonical(source).decode(),))
    reseal(root, change)
    with pytest.raises(StructuralError, match="pinned source completeness"):
        verify(root)


@pytest.mark.parametrize("variant", ["float-count", "float-source", "false-versus-zero"])
def test_manifest_requires_exact_json_types_against_database(tmp_path, variant):
    root = tmp_path / "field"
    make(root)
    if variant == "false-versus-zero":
        reseal(root, lambda db: db.execute("UPDATE meta SET value='0' WHERE key='authority_transfer'"))
    manifest = json.loads((root / "manifest.json").read_bytes())
    if variant == "float-count":
        manifest["counts"]["words"] = float(manifest["counts"]["words"])
    elif variant == "float-source":
        manifest["metadata"]["source"]["files"] = float(manifest["metadata"]["source"]["files"])
    else:
        manifest["metadata"]["authority_transfer"] = False
    (root / "manifest.json").write_bytes(canonical(manifest) + b"\n")
    with pytest.raises(StructuralError, match="receipt or manifest"):
        verify(root)
    with pytest.raises(StructuralError, match="receipt or manifest"):
        StructuralField(root)



@pytest.mark.parametrize("variant", ["pretty", "escaped", "duplicate-key", "leading-space",
                                     "trailing-space", "extra-newline", "missing-newline"])
def test_manifest_raw_bytes_must_be_canonical(tmp_path, variant):
    root = tmp_path / "field"
    make(root)
    path = root / "manifest.json"
    original = path.read_bytes()
    manifest = json.loads(original)
    assert original == canonical(manifest) + b"\n"
    if variant == "pretty":
        mutated = json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2).encode() + b"\n"
    elif variant == "escaped":
        mutated = original.replace(b"english-gonol", b"\\u0065nglish-gonol", 1)
    elif variant == "duplicate-key":
        mutated = b'{"schema":' + canonical(manifest["schema"]) + b"," + original[1:]
    elif variant == "leading-space":
        mutated = b" " + original
    elif variant == "trailing-space":
        mutated = original[:-1] + b" \n"
    elif variant == "extra-newline":
        mutated = original + b"\n"
    else:
        mutated = original[:-1]
    assert mutated != original and json.loads(mutated) == manifest
    path.write_bytes(mutated)
    with pytest.raises(StructuralError, match="noncanonical manifest"):
        verify(root)
    with pytest.raises(StructuralError, match="noncanonical manifest"):
        StructuralField(root)


def test_fresh_process_import_closure_is_fully_bound(tmp_path):
    from english_gonol import structural_construct as module
    package = Path(module.__file__).resolve().parent
    script = r"""
import importlib, json, sys
from pathlib import Path
package = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(package.parent))
for name in ("english_gonol.structural_construct", "english_gonol.structural_query"):
    importlib.import_module(name)
loaded = set()
for name, module in tuple(sys.modules.items()):
    filename = getattr(module, "__file__", None)
    if filename is None:
        continue
    path = Path(filename).resolve()
    if path.is_relative_to(package):
        loaded.add(path.relative_to(package).as_posix())
    elif name == "english_gonol" or name.startswith("english_gonol."):
        raise AssertionError(f"project import escaped expected package: {name}: {path}")
print(json.dumps(sorted(loaded)))
"""
    output = subprocess.check_output([sys.executable, "-I", "-c", script, str(package)],
                                     text=True, cwd=tmp_path)
    loaded = json.loads(output)
    assert len(module.IMPLEMENTATION_FILES) == len(set(module.IMPLEMENTATION_FILES))
    assert set(loaded) == set(module.IMPLEMENTATION_FILES)


@pytest.mark.parametrize("relative", [
    "language/__init__.py", "language/affixes.py", "language/manifest.py", "language/model.py",
    "language/morphology.py", "language/relational_bridge.py", "language/rendering.py",
])
def test_import_time_dependency_mutation_invalidates_implementation(tmp_path, relative):
    from english_gonol import structural_construct as module
    root = tmp_path / "field"
    make(root)
    package = tmp_path / "isolated" / "english_gonol"
    shutil.copytree(Path(module.__file__).resolve().parent, package,
                    ignore=shutil.ignore_patterns("__pycache__"))
    script = r"""
import sys
sys.path.insert(0, sys.argv[1])
from english_gonol.structural_construct import StructuralError, verify
try:
    verify(sys.argv[2])
except StructuralError as error:
    print(str(error))
    raise SystemExit(1)
"""
    command = [sys.executable, "-I", "-c", script, str(package.parent), str(root)]
    control = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert control.returncode == 0, control.stderr or control.stdout
    target = package / relative
    target.write_bytes(target.read_bytes() + b"\n# implementation identity mutation\n")
    mutated = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert mutated.returncode == 1
    assert mutated.stderr == ""
    assert mutated.stdout.strip() == "implementation mismatch; explicit migration required"
# ratios: loc_comments=920:197 imports_exports=39:69 calls_definitions=525:83
