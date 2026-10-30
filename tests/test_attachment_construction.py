# ratios: loc_comments=106:39 imports_exports=10:5 calls_definitions=70:5
# === CHECKS ===
# id: check_english_word_uses_native_attachment_and_exact_views
#   proves: english_attachment_native_authority
#   call: self::test_word_uses_native_attachment_and_exact_views
#   requires: pytest, pinned_ucns
#   mutates: none
#   cleanup: context_manager
# id: check_english_recursive_word_stack_requires_explicit_candidate
#   proves: english_attachment_bearing_boundary
#   call: self::test_recursive_word_stack_requires_explicit_candidate
#   requires: pytest, pinned_ucns
#   mutates: none
#   cleanup: context_manager
# id: check_english_compound_keeps_boundary_and_replays
#   proves: english_attachment_native_authority
#   call: self::test_compound_keeps_boundary_and_replays
#   requires: pytest, pinned_ucns
#   mutates: none
#   cleanup: context_manager
# id: check_english_no_false_native_or_carrier_provenance
#   proves: english_attachment_native_authority
#   call: self::test_no_false_native_or_carrier_provenance
#   requires: pytest, pinned_ucns
#   mutates: filesystem
#   cleanup: pytest_fixture_teardown
# id: check_english_partial_corpus_and_whole_lexical_owner
#   proves: english_attachment_source_structure, english_attachment_lexical_owner
#   call: self::test_partial_corpus_and_whole_lexical_owner
#   requires: pytest, pinned_ucns
#   mutates: filesystem
#   cleanup: pytest_fixture_teardown
# === END CHECKS ===
# SPDX-License-Identifier: FSL-1.1-ALv2
# Copyright 2026 Erin Spencer
"""Native consumer tests: pytest -c /dev/null ordinal_tests/test_attachment_construction.py.

GPT generated; context, prompt Erin Spencer.
Corpus fixtures test admission refusals and typed ownership only; no partial
fixture is represented as verified Public Gonol corpus geometry.
"""
from copy import deepcopy
from fractions import Fraction
import json

import pytest

from english_gonol import attachment_construction as api
from english_gonol.ordinal_construction import OrdinalGeometryError
from english_gonol.language.source import LexemeRecord, SenseRecord, SynsetRecord, WordnetSnapshot
from english_gonol.structural_construct import build
from ucns.attachment_stack import DiskStack, Closed, stack, display
from ucns.attachment_codec import export_graph, replay_graph


def test_word_uses_native_attachment_and_exact_views():
    word = api.construct_word('bull')
    assert isinstance(word, DiskStack)
    assert [r.radius for r in word.rays] == [Fraction(1, 16), Fraction(1, 8), Fraction(1, 4), Fraction(1, 2)]
    assert [r.heading.turn for r in word.rays] == [Fraction(i, 157) for i in (83, 66, 22, 135)]
    packet = json.loads(json.dumps(api.word_record(word)))
    assert packet['geometry_authority'] == api.authority()
    assert replay_graph(packet['graph']).recover() == tuple('bull')
    assert packet['disk_depths'] == [4, 3, 2, 1]


def test_recursive_word_stack_requires_explicit_candidate():
    words = tuple(api.construct_word(w) for w in ('on', 'the', 'on'))
    with pytest.raises(OrdinalGeometryError, match='CLOSED_WORD_BEARING_POLICY_REQUIRED'):
        api.construct_sequence(words)
    for policy in ('root-endpoint-v1', 'exit-heading-v1'):
        obj = api.construct_sequence(words, bearing=policy)
        assert [obj.depth(i) for i in range(3)] == [3, 2, 1]
        assert obj.recover() == tuple('ontheon')
        assert obj.participants[0].interior is words[0]
        assert replay_graph(export_graph(obj)).recover() == obj.recover()
        assert abs(display(obj.endpoint)) > 0
    with pytest.raises(OrdinalGeometryError, match='CLOSED_WORD_PARTICIPANTS_REQUIRED'):
        api.construct_sequence((), bearing='exit-heading-v1')


def test_compound_keeps_boundary_and_replays():
    left, right = api.construct_word('bull'), api.construct_word('shit')
    record = api.construct_compound(left, right)
    assert record['attachment_ordinal'] == 3
    assert api.replay_compound(json.loads(json.dumps(record))) == record
    assert record['components'][0]['graph']['root'] == left.receipt
    assert record['components'][1]['graph']['root'] == right.receipt
    compound = replay_graph(record['graph'])
    for policy in ('root-endpoint-v1', 'exit-heading-v1'):
        parent = api.construct_sequence((compound, left), bearing=policy)
        assert parent.recover() == tuple('bullshitbull')
    for mutate in (
        lambda r: r.update(attachment_ordinal=2),
        lambda r: r['components'].reverse(),
        lambda r: r['incoming_rows'][0].update(origin=[]),
        lambda r: r['geometry_authority'].update(commit='0' * 40),
    ):
        bad = deepcopy(record); mutate(bad)
        with pytest.raises(OrdinalGeometryError, match='COMPOUND_REPLAY_MISMATCH'):
            api.replay_compound(bad)


def test_no_false_native_or_carrier_provenance(tmp_path, monkeypatch):
    native, _codec = api._native()
    forged = tmp_path / 'producer.py'; forged.write_text('changed producer\n')
    with monkeypatch.context() as patch:
        patch.setattr(native, '__file__', str(forged))
        api._native.cache_clear()
        with pytest.raises(OrdinalGeometryError, match='UCNS_ATTACHMENT_PRODUCER_DRIFT'):
            api.construct_word('word')
    api._native.cache_clear()
    with monkeypatch.context() as patch:
        patch.setattr(native, '__file__', str(tmp_path / 'missing.py'))
        api._native.cache_clear()
        with pytest.raises(OrdinalGeometryError, match='UCNS_ATTACHMENT_PRODUCER_REQUIRED'):
            api.construct_word('word')
    api._native.cache_clear()
    importer = api.importlib.import_module
    with monkeypatch.context() as patch:
        def missing(name):
            if name == 'ucns.attachment_stack':
                raise ModuleNotFoundError(name)
            return importer(name)
        patch.setattr(api.importlib, 'import_module', missing)
        api._native.cache_clear()
        with pytest.raises(OrdinalGeometryError, match='UCNS_ATTACHMENT_PRODUCER_REQUIRED'):
            api.construct_word('word')
    api._native.cache_clear()
    for text in ('word word', 'é', '🦄', ''):
        with pytest.raises(OrdinalGeometryError):
            api.construct_word(text)
    word = api.construct_word('word')
    other = stack(word.identity, word.participants, relation='unrelated', source=word.source)
    with pytest.raises(OrdinalGeometryError, match='PUBLIC_GONOL_WORD_STACK_REQUIRED'):
        api.word_record(other)


def test_partial_corpus_and_whole_lexical_owner(tmp_path):
    source = WordnetSnapshot(
        lexemes=(LexemeRecord('bull shit', 'n', (), (SenseRecord('s1', 'n1', ()),)),),
        synsets=(SynsetRecord('n1', 'n', ('bull shit',), ('bull shit.',), ()),),
        source_tree_sha256='0' * 64, source_file_count=1)
    output = tmp_path / 'fixture'
    build(source, out_dir=output, public_position=lambda _c: None, producer={'standing': 'fixture-only'})
    with api.RecursiveStructuralField(output, bearing='exit-heading-v1') as field:
        query = field.construct(' bull  shit. ')
        assert field.geometry(query, operation='recursive-stack')['code'] == 'COMPLETE_CORPUS_REQUIRED_FOR_PUBLIC_GONOL'
        assert field.compose(field.construct('bull shit'), relation='sentence')['code'] == 'SENTENCE_CLOSURE_UNRESOLVED'
        rid = field.db.execute("SELECT id FROM records WHERE kind='definition'").fetchone()[0]
        definition = field.definition(rid)
        owner = definition['lexical_owner']
        assert owner['kind'] == 'lexical-construction' and owner['text'] == 'bull shit'
        assert [p['kind'] for p in owner['parts']] == ['word', 'character', 'word']
        assert definition['origin']['owner_record_id'] == owner['record_id']
        assert 'word_id' not in definition['origin']
        assert definition['definition_succession']['ordinal'] == 0
        assert definition['historical_origin']['state'] == 'hmmm:compound-lexical-origin'
        assert all(p['owner'] == definition['origin'] for p in definition['constituent_direct'])
# ratios: loc_comments=106:39 imports_exports=10:5 calls_definitions=70:5
