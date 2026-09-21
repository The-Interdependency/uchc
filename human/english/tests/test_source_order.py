# === CHECKS ===
# id: check_oewn_source_preserves_sense_order
#   proves: oewn_source_preserves_sense_order
#   call: self::test_loader_preserves_source_sense_order
#   requires: python3
#   timeout: 30
#   mutates: filesystem
#   cleanup: tempdir_teardown
# === END CHECKS ===

from __future__ import annotations

from pathlib import Path

import pytest

import english_gonol.language.source as source


def test_loader_preserves_source_sense_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The identifiers are intentionally reverse-lexicographic. Sorting them
    # would silently destroy the source ordinal evidence used by construction.
    for name in ("frames.yaml", "entries-test.yaml", "noun.test.yaml"):
        (tmp_path / name).write_text("fixture\n", encoding="utf-8")

    documents = {
        "frames.yaml": {},
        "entries-test.yaml": {
            "word": {
                "n": {
                    "sense": [
                        {"id": "z-sense", "synset": "s-z"},
                        {"id": "a-sense", "synset": "s-a"},
                    ]
                }
            }
        },
        "noun.test.yaml": {
            "s-z": {
                "partOfSpeech": "n",
                "members": ["word"],
                "definition": ["first definition"],
            },
            "s-a": {
                "partOfSpeech": "n",
                "members": ["word"],
                "definition": ["second definition"],
            },
        },
    }

    def fake_load_yaml(path: Path):
        return documents[path.name]

    monkeypatch.setattr(source, "_load_yaml", fake_load_yaml)
    monkeypatch.setattr(source, "OEWN_EXPECTED_WORD_COUNT", 1)
    monkeypatch.setattr(source, "OEWN_EXPECTED_SYNSET_COUNT", 2)

    snapshot = source.load_oewn_2025(tmp_path)
    assert len(snapshot.lexemes) == 1
    assert [sense.sense_id for sense in snapshot.lexemes[0].senses] == [
        "z-sense",
        "a-sense",
    ]
