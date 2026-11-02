# === CHECKS ===
# id: check_metric_origin_instrument_boundary
#   proves: metric_origin_words_define_instrument_not_evidence
#   call: self::test_origin_record_contains_no_measurement_value
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_metric_origin_order_provenance
#   proves: metric_origin_preserves_order_identity_provenance
#   call: self::test_resolved_origin_uses_word_and_glyph_axes_in_order
#   requires: python3
#   timeout: 10
#   mutates: temporary sqlite fixture
#   cleanup: pytest tmp_path
#
# id: check_metric_origin_construct_identity
#   proves: metric_origin_preserves_order_identity_provenance
#   call: self::test_wrong_construct_receipt_fails_closed
#   requires: python3
#   timeout: 10
#   mutates: temporary sqlite fixture
#   cleanup: pytest tmp_path
#
# id: check_metric_origin_hmmm
#   proves: metric_origin_unresolved_fails_open_as_hmmm_not_closed
#   call: self::test_unresolved_origin_does_not_construct_components
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_metric_origin_receipt_schema
#   proves: metric_origin_receipt_binds_schema
#   call: self::test_receipt_hashes_complete_payload_except_receipt
#   requires: python3
#   timeout: 10
#   mutates: temporary sqlite fixture
#   cleanup: pytest tmp_path
# id: check_metric_origin_pinned_corpus_admission
#   proves: metric_origin_terms_admitted_by_pinned_corpus
#   call: self::test_all_resolved_terms_are_admitted_by_pinned_oewn
#   requires: python3, PyYAML, exact OEWN 2025 source
#   timeout: 60
#   mutates: none
#   cleanup: none
# id: check_metric_origin_source_fixture
#   proves: metric_origin_source_fixture_matches_pinned_edcm
#   call: self::test_stack_fixture_matches_exact_edcm_producer
#   requires: python3, exact EDCM metric-origin producer
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from hashlib import sha256
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

import english_gonol.edcm_metric_origins as origins
from english_gonol.hyperspace_construct import V2_MANIFEST_RECEIPT
from english_gonol.full_construct_run import _collect_surfaces, verify_replay
from english_gonol.language.source import load_oewn_2025, OEWN_COMMIT


def _fixture(tmp_path: Path):
    path = tmp_path / "source.json"
    path.write_bytes(origins.FIXTURE.read_bytes())
    return path


def _source_root(variable):
    root = os.environ.get(variable)
    if not root:
        if os.environ.get("REQUIRE_METRIC_ORIGIN_SOURCES") == "1":
            pytest.fail(f"required provenance source missing: {variable}")
        pytest.skip(f"{variable} not supplied for optional local replay")
    return Path(root)


def _verify_checkout(root, commit, paths):
    assert subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip() == commit
    subprocess.run(["git", "-C", str(root), "diff", "--exit-code", "HEAD", "--", *paths], check=True)


def _db(tmp_path: Path):
    db=sqlite3.connect(tmp_path/"construct.db")
    db.executescript("""
    CREATE TABLE characters (id INTEGER PRIMARY KEY, scalar TEXT, public_position INTEGER);
    CREATE TABLE words (id INTEGER PRIMARY KEY, surface TEXT);
    CREATE TABLE word_characters (word_id INTEGER, ordinal INTEGER, character_id INTEGER);
    """)
    chars={}
    next_id=1
    words=["fixation","persistence","repetition"]
    for surface in words:
        for ch in surface+" ":
            if ch not in chars:
                chars[ch]=next_id
                db.execute("INSERT INTO characters VALUES (?,?,NULL)",(next_id,ch))
                next_id+=1
    for wid,surface in enumerate(words,1):
        db.execute("INSERT INTO words VALUES (?,?)",(wid,surface))
        for ordinal,ch in enumerate(surface):
            db.execute("INSERT INTO word_characters VALUES (?,?,?)",(wid,ordinal,chars[ch]))
    db.commit(); db.close()


def _verified(monkeypatch):
    monkeypatch.setattr(origins, "_assert_schema_boundary", lambda _db: None)
    monkeypatch.setattr(origins, "_logical_receipt", lambda _db: V2_MANIFEST_RECEIPT)


def test_resolved_origin_uses_word_and_glyph_axes_in_order(tmp_path, monkeypatch):
    _db(tmp_path); _verified(monkeypatch)
    record=origins.build_metric_origin_set(tmp_path,"F",fixture_path=_fixture(tmp_path))
    assert record.closed
    assert record.construct_receipt==V2_MANIFEST_RECEIPT
    assert record.source_text=="fixation persistence repetition"
    assert record.components[0].axis_origin=="O_W"
    assert any(x.axis_origin=="O_G" and x.surface==" " for x in record.components)
    assert record.producer_repository=="The-Interdependency/edcm"
    assert "maintained implementation is a lexical structural proxy, not embedding similarity" in record.unresolved
    assert record.carrier_id == "F"
    assert record.metric_id == "edcm.behavioral.F.fixation"
    assert record.origin_id == "O_M(edcm.behavioral.F.fixation)"


def test_origin_record_contains_no_measurement_value(tmp_path, monkeypatch):
    _db(tmp_path); _verified(monkeypatch)
    record=origins.build_metric_origin_set(tmp_path,"F",fixture_path=_fixture(tmp_path))
    keys=record.to_dict()
    assert "value" not in keys
    assert "measurement" not in keys
    assert "score" not in keys
    assert record.source_text=="fixation persistence repetition"


def test_wrong_construct_receipt_fails_closed(tmp_path, monkeypatch):
    _db(tmp_path)
    monkeypatch.setattr(origins, "_assert_schema_boundary", lambda _db: None)
    monkeypatch.setattr(origins, "_logical_receipt", lambda _db: "0"*64)
    with pytest.raises(ValueError,match="construct receipt mismatch"):
        origins.build_metric_origin_set(tmp_path,"F",fixture_path=_fixture(tmp_path))


def test_o_l_source_split_is_resolved_without_aliasing():
    fixture=origins.load_metric_origin_specs()
    o=fixture["specs"]["O"]
    l=fixture["specs"]["L"]
    assert o["standing"]=="resolved"
    assert l["standing"]=="resolved"
    assert o["canonical_metric_id"]=="edcm.behavioral.O_scope"
    assert l["canonical_metric_id"]=="edcm.behavioral.L_loss"
    assert "O_confidence" in o["unresolved"][0]
    assert "L_load" in l["unresolved"][0]
    assert "L_resistance" in l["unresolved"][0]


def test_unresolved_origin_does_not_construct_components(tmp_path, monkeypatch):
    path=_fixture(tmp_path)
    source=json.loads(path.read_text())
    source["specs"]["O"]["standing"]="hmmm"
    source["specs"]["O"]["construction_terms"]=[]
    source["specs"]["O"]["unresolved"]=["synthetic unresolved boundary"]
    path.write_text(json.dumps(source, indent=2) + "\n")
    monkeypatch.setattr(origins, "FIXTURE_SHA256", sha256(path.read_bytes()).hexdigest())
    record=origins.build_metric_origin_set(tmp_path,"O",fixture_path=path)
    assert record.carrier_id=="O"
    assert record.metric_id=="edcm.behavioral.O_scope"
    assert record.closed is False
    assert record.components==()
    assert record.construct_receipt=="hmmm"
    assert record.unresolved==("synthetic unresolved boundary",)
    assert record.origin_id=="O_M(edcm.behavioral.O_scope)"


def test_receipt_hashes_complete_payload_except_receipt(tmp_path, monkeypatch):
    _db(tmp_path); _verified(monkeypatch)
    record=origins.build_metric_origin_set(tmp_path,"F",fixture_path=_fixture(tmp_path))
    payload=record.to_dict()
    receipt=payload.pop("receipt_sha256")
    expected=sha256(json.dumps(
        payload,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False
    ).encode("utf-8")).hexdigest()
    assert receipt==expected
    assert payload["schema"]==origins.SCHEMA
    assert payload["version"]==origins.VERSION


def test_all_resolved_terms_are_admitted_by_pinned_oewn():
    root = _source_root("OEWN_SOURCE_ROOT")
    _verify_checkout(root, OEWN_COMMIT, ["."])
    snapshot=load_oewn_2025(root)
    words,_characters=_collect_surfaces(snapshot)
    admitted=set(words)
    fixture=origins.load_metric_origin_specs()
    missing={}
    for metric,spec in fixture["specs"].items():
        if spec["standing"]!="resolved":
            continue
        absent=[term for term in spec["construction_terms"] if term not in admitted]
        if absent:
            missing[metric]=absent
    assert missing=={}


def test_stack_fixture_matches_exact_edcm_producer():
    root = _source_root("EDCM_METRIC_ORIGIN_ROOT")
    fixture=origins.load_metric_origin_specs()
    _verify_checkout(root, fixture["producer_commit"], ["edcm"] )
    module_path=Path(root)/"edcm"/"metric_origin_spec.py"
    spec=importlib.util.spec_from_file_location("_pinned_edcm_metric_origin_spec",module_path)
    assert spec is not None and spec.loader is not None
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    fixture=origins.load_metric_origin_specs()
    assert fixture["producer_commit"]=="0873c105799681ea1f7ccb3e619d1f7aebbd85e0"
    assert tuple(fixture["specs"])==tuple(module.METRIC_ORIGIN_SPECS)
    for metric,source_spec in module.METRIC_ORIGIN_SPECS.items():
        record=fixture["specs"][metric]
        assert record["canonical_metric_id"]==source_spec.canonical_metric_id
        assert record["surface_terms"]==list(source_spec.surface_terms)
        assert record["construction_terms"]==list(source_spec.construction_terms)
        assert record["semantic_definition"]==source_spec.semantic_definition
        assert record["standing"]==source_spec.standing
        assert record["measurement_alignment"]==source_spec.measurement_alignment
        assert record["unresolved"]==list(source_spec.unresolved)


@pytest.mark.parametrize("mutation", ["repository", "commit", "terms", "standing"])
def test_unregistered_or_modified_fixture_fails_closed(tmp_path, mutation):
    path = _fixture(tmp_path)
    source = json.loads(path.read_text())
    if mutation == "repository":
        source["producer_repository"] = "someone/else"
    elif mutation == "commit":
        source["producer_commit"] = "a" * 40
    elif mutation == "terms":
        source["specs"]["F"]["construction_terms"] = ["invented"]
    else:
        source["specs"]["O"]["standing"] = "resolved"
    path.write_text(json.dumps(source))
    with pytest.raises(ValueError, match="fixture digest mismatch"):
        origins.build_metric_origin_set(tmp_path, "F", fixture_path=path)


def test_packaged_producer_registration_agrees():
    fixture = origins.load_metric_origin_specs()
    registered = json.loads(origins.BASE.read_text())["metric_origin_source"]
    assert registered["repository"] == fixture["producer_repository"]
    assert registered["commit"] == fixture["producer_commit"]
    assert registered["authority_transfer"] is False


def test_required_provenance_source_cannot_skip(monkeypatch):
    monkeypatch.setenv("REQUIRE_METRIC_ORIGIN_SOURCES", "1")
    monkeypatch.delenv("OEWN_SOURCE_ROOT", raising=False)
    with pytest.raises(pytest.fail.Exception, match="required provenance source missing"):
        _source_root("OEWN_SOURCE_ROOT")


def test_full_construct_origins_bind_to_pinned_edcm():
    state_dir = _source_root("ENGLISH_GONOL_FULL_CONSTRUCT_ROOT")
    edcm_root = _source_root("EDCM_METRIC_ORIGIN_ROOT")
    fixture = origins.load_metric_origin_specs()
    _verify_checkout(edcm_root, fixture["producer_commit"], ["edcm"])
    manifest = verify_replay(state_dir)
    assert manifest["receipt_sha256"] == V2_MANIFEST_RECEIPT
    records = {metric: origins.build_metric_origin_set(state_dir, metric).to_dict()
               for metric in fixture["specs"]}
    for metric, record in records.items():
        payload = {k: v for k, v in record.items() if k != "receipt_sha256"}
        assert sha256(origins._canonical(payload)).hexdigest() == record["receipt_sha256"]
        canonical = fixture["specs"][metric]["canonical_metric_id"]
        assert record["carrier_id"] == metric
        assert record["metric_id"] == canonical
        assert record["origin_id"] == f"O_M({canonical})"
        assert record["closed"] is True
    # A subprocess prevents an already-imported editable EDCM from shadowing
    # the exact producer checkout under test.
    result = subprocess.run(
        [sys.executable, "-c", """
import json, sys
from dataclasses import asdict
from edcm.measurement import compute_transcript, parse_transcript
from edcm.semantic_metric_space import build_semantic_metric_space, bind_round_metrics
origins = json.load(sys.stdin)
space = build_semantic_metric_space(origins)
assert space.unresolved_metrics == ()
assert space.complete
metrics = compute_transcript(parse_transcript('A: State the constraint.\\nB: Recorded.'))[0]
rows = bind_round_metrics(metrics, space, evidence_receipt='synthetic-transcript:full-replay-test')
assert [row.value for row in rows] == metrics.vector()
assert all(row.semantic_projection == 'hmmm' for row in rows)
print(json.dumps([asdict(row) for row in rows], allow_nan=False))
"""], cwd=edcm_root, input=json.dumps(records), text=True, capture_output=True,
        env={**os.environ, "PYTHONPATH": str(edcm_root)}, check=True,
    )
    evidence = {"producer_commit": fixture["producer_commit"],
                "construct_receipt": manifest["receipt_sha256"],
                "origin_records": records, "readouts": json.loads(result.stdout),
                "unresolved_metrics": [], "semantic_projection": "hmmm"}
    (state_dir / "metric-origin-replay.json").write_text(json.dumps(evidence, indent=2) + "\n")
