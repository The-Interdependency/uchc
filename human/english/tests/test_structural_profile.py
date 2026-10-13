# ratios: loc_comments=230:29 imports_exports=11:25 calls_definitions=125:27
"""Witnesses for the accepted thirteen-rule profile, including hostile records."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import sqlite3

import pytest

from english_gonol.language.source import LexemeRecord, SenseRecord, SynsetRecord, WordnetSnapshot
from english_gonol.structural_rules import segment, canonical
from english_gonol.structural_construct import StructuralError, build, verify, _manifest
from english_gonol.structural_query import StructuralField

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
    (root / "manifest.json").write_bytes(canonical(manifest))
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
    (root / "manifest.json").write_bytes(canonical(manifest))


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
    reseal(root, lambda db: db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (key, json.dumps(value))))
    with pytest.raises(StructuralError):
        verify(root)


def test_resealed_pinned_source_claim_requires_all_evidence(tmp_path):
    from english_gonol.structural_construct import PINNED_SOURCE
    root = tmp_path / "state"
    make(root)
    def change(db):
        db.execute("UPDATE meta SET value=? WHERE key='source'", (json.dumps(PINNED_SOURCE),))
        db.execute("UPDATE meta SET value='true' WHERE key='complete_corpus'")
    reseal(root, change)
    with pytest.raises(StructuralError, match="source evidence digest"):
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
        db.execute("UPDATE evidence SET payload=? WHERE kind=? AND ordinal=0", (json.dumps(payload), kind))
    reseal(root, change)
    with pytest.raises(StructuralError, match="source evidence digest"):
        verify(root)


@pytest.fixture
def punctuation_field(tmp_path):
    source = snapshot()
    source = replace(source, synsets=source.synsets + (
        SynsetRecord("punctuation", "n", ("geometry",), ('"geometry." (geometry!?) [geometry.] {geometry!} “geometry?” geometry; geometry,',), ()),))
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
# ratios: loc_comments=230:29 imports_exports=11:25 calls_definitions=125:27
