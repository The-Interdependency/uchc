# ratios: loc_comments=152:22 imports_exports=10:7 calls_definitions=106:8
"""Run: python -m pytest -q human/english/tests/test_inference_input.py.

Fixtures exercise implementation contracts, never claim full-corpus acceptance.
"""
# === CHECKS ===
# id: uchc_input_source_witness
#   proves: uchc_input_preserves_source
#   call: self::test_exact_source_and_unknowns
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: uchc_input_native_witness
#   proves: uchc_input_consumes_native_construction
#   call: self::test_native_words_definitions_and_evidence
#   mutates: filesystem
#   cleanup: tempdir_teardown
# id: uchc_input_tamper_witness
#   proves: uchc_input_fails_closed
#   call: self::test_artifact_snapshot_and_replay_fail_closed
#   mutates: filesystem
#   cleanup: tempdir_teardown
# === END CHECKS ===
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

import pytest

from english_gonol.full_construct_run import build_construct
from english_gonol.hyperspace_construct import GlyphGonol, WordGonol, DefinitionGonol
from english_gonol.inference_input import EnglishConstruct, ConstructError, AdmissionError
from english_gonol.language.source import LexemeRecord, SenseRecord, SynsetRecord, WordnetSnapshot


@pytest.fixture
def artifact(tmp_path):
    snapshot = WordnetSnapshot(
        lexemes=(
            LexemeRecord('alpha', 'n', (), (
                SenseRecord('s1', 'one', (('also', ('s3',)),)),
                SenseRecord('s2', 'two', (('also', ('missing',)),)),
            )),
            LexemeRecord('other', 'n', (), (SenseRecord('s3', 'three', ()),)),
            LexemeRecord('multi word', 'n', (), ()),
        ),
        synsets=(
            SynsetRecord('one', 'n', ('alpha',), ('alpha letter alpha.',), ()),
            SynsetRecord('two', 'n', ('alpha',), ('é\talpha\r\n',), ()),
            SynsetRecord('three', 'n', ('other',), ('another word',), ()),
        ), source_tree_sha256='0' * 64, source_file_count=3,
    )
    path = tmp_path / 'construct.db'
    result = build_construct(snapshot, db_path=path, public_position=lambda c: None)
    return path, sha256(path.read_bytes()).hexdigest(), result['receipt_sha256'], result['counts']


def _open(artifact):
    path, digest, logical, _counts = artifact
    return EnglishConstruct(path, database_sha256=digest, logical_receipt=logical)


def test_exact_source_and_unknowns(artifact):
    with _open(artifact) as corpus:
        text = 'alpha\talpha é\r\n🧪α Alpha alpha!'
        frame = corpus.resolve_text(text, source_id='fixture:exact')
        assert frame.text == text and frame.recover_utf8() == text.encode()
        assert len(frame.glyphs) == len(text)
        for i, glyph in enumerate(frame.glyphs):
            assert glyph.ordinal == i and glyph.scalar == text[i]
            assert text.encode()[glyph.utf8_start:glyph.utf8_end].decode() == glyph.scalar
        assert frame.glyphs[0].gonol is frame.glyphs[6].gonol
        assert len([word for word in frame.words if word.gonol.surface == 'alpha']) == 1
        assert not frame.glyphs_admitted and not frame.words_admitted
        unknowns = [o.surface for o in frame.occurrences if o.identity_id is None]
        assert unknowns == ['🧪α', 'Alpha', 'alpha!']
        with pytest.raises(AdmissionError):
            frame.require_complete()
        assert corpus.resolve_utf8(text.encode(), source_id=frame.source_id) == frame
        assert corpus.replay(frame.to_bytes()) == frame
        assert corpus.resolve_text('alpha letter alpha.', source_id='f').require_complete()
        assert corpus.resolve_text('', source_id='empty').recover_utf8() == b''
        # Exact lexical lookup, not invented phrase parsing or normalization.
        assert corpus.word('multi word').gonol.surface == 'multi word'
        assert corpus.word('Alpha') is None and corpus.word('e\u0301') is None


def test_native_words_definitions_and_evidence(artifact):
    with _open(artifact) as corpus:
        alpha = corpus.word('alpha')
        assert type(alpha.gonol) is WordGonol
        assert alpha.construct_receipt == corpus.identity.logical_receipt
        assert len(alpha.definition_ids) == 2
        first, second = [corpus.definition(i) for i in alpha.definition_ids]
        assert type(first.gonol) is DefinitionGonol
        assert first.gonol.origin_word_id == alpha.gonol.word_id
        assert second.gonol.origin_word_id == alpha.gonol.word_id
        assert first.previous_definition_id is None
        assert second.previous_definition_id == first.gonol.definition_id
        assert (first.sense_id, second.sense_id) == ('s1', 's2')
        assert first.gonol.axis_index != second.gonol.axis_index
        assert corpus.recover_definition(first) == 'alpha letter alpha.'
        assert corpus.recover_definition(second) == 'é\talpha\r\n'
        assert any(e.relation == 'also' and e.target_ref == 's3' for e in first.evidence)
        assert any(e.status == 'unresolved' and e.target_ref == 'missing' for e in second.evidence)
        assert tuple((c.kind, c.identity_id) for c in first.components) == first.gonol.constituent_ids
        assert all(type(g) is GlyphGonol for g in corpus.inventory.values())
        assert len(list(corpus.iter_words())) == artifact[3]['words']
        assert len(list(corpus.iter_definitions())) == artifact[3]['definitions']
        frame = corpus.resolve_text('alpha alpha', source_id='same')
        assert frame.words[0].definition_ids == alpha.definition_ids
        wire = frame.to_dict()
        assert len(wire['glyphs']) == len(set(frame.text))
        assert len(wire['glyph_occurrences']) == len(frame.text)
        assert frame.to_dict()['sense_selection'].startswith('unresolved')
        with pytest.raises(ConstructError):
            corpus.recover_definition(replace(first, construct_receipt='0' * 64))
        with pytest.raises(ConstructError):
            corpus.recover_definition(replace(first, text='changed'))
        # Transport dictionaries are copies; mutation cannot edit native state.
        payload = frame.to_dict()
        payload['words'].clear()
        assert frame.words and corpus.replay(frame.to_bytes()) == frame


def test_artifact_snapshot_and_replay_fail_closed(artifact):
    path, digest, logical, counts = artifact
    with pytest.raises(ConstructError, match='byte identity'):
        EnglishConstruct(path, database_sha256='0' * 64, logical_receipt=logical)
    with pytest.raises(ConstructError, match='logical receipt'):
        EnglishConstruct(path, database_sha256=digest, logical_receipt='0' * 64)
    with pytest.raises(ConstructError):
        EnglishConstruct(path.parent / 'absent.db', database_sha256=digest, logical_receipt=logical)
    assert not (path.parent / 'absent.db').exists()
    corpus = _open(artifact)
    frame = corpus.resolve_text('alpha alpha', source_id='fixture:replay')
    private = Path(corpus._temporary.name)
    with sqlite3.connect(path) as db:
        db.execute("UPDATE words SET surface='tampered' WHERE surface='alpha'")
    assert corpus.resolve_text(frame.text, source_id=frame.source_id) == frame
    with pytest.raises(sqlite3.OperationalError):
        corpus._connection().execute("DELETE FROM words")
    for field, value in [('version', 'changed'), ('glyphs_admitted', 1),
                         ('receipt_sha256', '0' * 64), ('extra', True)]:
        payload = frame.to_dict(); payload[field] = value
        data = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
        with pytest.raises(ConstructError):
            corpus.replay(data)
    payload = frame.to_dict(); payload['occurrences'][0]['identity_id'] = 999
    with pytest.raises(ConstructError):
        corpus.replay(json.dumps(payload).encode())
    for data in [b'[]', b'null', b'{}', b'\xff', b'{broken']:
        with pytest.raises(ConstructError):
            corpus.replay(data)
    corpus.close(); corpus.close()
    assert not private.exists()
    with pytest.raises(ConstructError, match='closed'):
        corpus.resolve_text('alpha', source_id='closed')


@pytest.mark.parametrize('value', [None, 3, ['alpha'], b'alpha'])
def test_text_never_coerces(artifact, value):
    with _open(artifact) as corpus:
        with pytest.raises(TypeError):
            corpus.resolve_text(value, source_id='invalid')


@pytest.mark.parametrize('value', [True, False, 1.0, '1', 0, -1])
def test_id_never_coerces(artifact, value):
    with _open(artifact) as corpus:
        with pytest.raises(ConstructError):
            corpus.word_by_id(value)
        with pytest.raises(ConstructError):
            corpus.definition(value)


def test_invalid_unicode_and_identity(artifact):
    with _open(artifact) as corpus:
        for text in ['\ud800', 'a\udfff']:
            with pytest.raises(ConstructError):
                corpus.resolve_text(text, source_id='invalid')
        with pytest.raises(ConstructError):
            corpus.resolve_text('alpha', source_id='')
        with pytest.raises(UnicodeDecodeError):
            corpus.resolve_utf8(b'\xff', source_id='bad')
        with pytest.raises(TypeError):
            corpus.resolve_utf8('alpha', source_id='bad')
        with pytest.raises(TypeError):
            corpus.replay({})
        with pytest.raises(ValueError):
            corpus.word_by_id(999999)
        with pytest.raises(ValueError):
            corpus.definition(999999)
# ratios: loc_comments=152:22 imports_exports=10:7 calls_definitions=106:8
