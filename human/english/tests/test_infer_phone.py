# === CHECKS ===
# id: check_infer_phone_calls_respond
#   proves: infer_phone_calls_respond
#   call: self::test_calls_respond
#   requires: python3, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_infer_phone_empty_is_empty_card
#   proves: infer_phone_empty_is_empty_card
#   call: self::test_empty_is_empty_card
#   requires: python3
#   timeout: 30
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: check_infer_phone_fails_closed
#   proves: infer_phone_fails_closed
#   call: self::test_fails_closed
#   requires: python3
#   timeout: 30
#   mutates: filesystem
#   cleanup: tempdir_teardown
# === END CHECKS ===
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from english_gonol.full_construct_run import build_construct
from english_gonol.infer_phone import build_response_card, run_phone
from english_gonol.language.source import LexemeRecord, SenseRecord, SynsetRecord, WordnetSnapshot

UCNS_SOURCE_ROOT = Path(os.environ.get("UCNS_SOURCE_ROOT", "/tmp/ucns-infer"))


@pytest.fixture
def artifact(tmp_path):
    snapshot = WordnetSnapshot(
        lexemes=(
            LexemeRecord("alpha", "n", (), (
                SenseRecord("s1", "one", (("also", ("s3",)),)),
                SenseRecord("s2", "two", (("also", ("missing",)),)),
            )),
            LexemeRecord("other", "n", (), (SenseRecord("s3", "three", ()),)),
        ),
        synsets=(
            SynsetRecord("one", "n", ("alpha",), ("alpha letter alpha.",), ()),
            SynsetRecord("two", "n", ("alpha",), ("other word",), ()),
            SynsetRecord("three", "n", ("other",), ("another word",), ()),
        ),
        source_tree_sha256="0" * 64,
        source_file_count=3,
    )
    path = tmp_path / "construct.db"
    result = build_construct(snapshot, db_path=path, public_position=lambda c: None)
    return str(path), sha256(path.read_bytes()).hexdigest(), result["receipt_sha256"]


def _argv(artifact, text, **extra):
    path, digest, logical = artifact
    args = [text, "--construct-db", path, "--database-sha256", digest,
            "--logical-receipt", logical, "--ucns-source-root", str(UCNS_SOURCE_ROOT)]
    for key, value in extra.items():
        args += [f"--{key.replace('_', '-')}", value]
    return args


def test_calls_respond(artifact):
    path, digest, logical = artifact
    card = build_response_card(
        "alpha letter alpha.", Path(path), digest, logical, UCNS_SOURCE_ROOT)
    assert card["words"] == ["alpha", "letter", "alpha."]
    assert card["motion_card"]["sample_not_selected"] is True
    assert card["bundle_count_hidden"] > 0


def test_empty_is_empty_card(artifact, capsys):
    code = run_phone(_argv(artifact, ""))
    out = capsys.readouterr().out
    assert code == 0
    card = json.loads(out)
    assert card["motion_card"] is None
    assert card["empty_is_not_an_answer"] is True


def test_fails_closed(artifact, capsys):
    path, digest, logical = artifact
    bad_args = ["alpha", "--construct-db", path, "--database-sha256", "0" * 64,
                "--logical-receipt", logical, "--ucns-source-root", str(UCNS_SOURCE_ROOT)]
    code = run_phone(bad_args)
    out, err = capsys.readouterr()
    assert code == 1
    assert out == ""
    assert "infer-phone:" in err

    refused = run_phone(_argv(artifact, "alpha letter alpha.", K="other"))
    card = json.loads(capsys.readouterr().out)
    assert refused == 0
    assert card["refuse"][0]["clause"].startswith("not determined")
