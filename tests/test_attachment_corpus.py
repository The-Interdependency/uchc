# ratios: loc_comments=56:27 imports_exports=5:4 calls_definitions=22:4
# === CHECKS ===
# id: check_english_complete_query_retains_source_and_occurrences
#   proves: english_attachment_source_structure
#   call: self::test_complete_query_retains_source_and_occurrences
#   requires: pytest, pinned_ucns
#   mutates: none
#   cleanup: context_manager
# id: check_english_no_policy_is_a_narrow_bearing_boundary
#   proves: english_attachment_bearing_boundary
#   call: self::test_no_policy_is_a_narrow_bearing_boundary
#   requires: pytest, pinned_ucns
#   mutates: none
#   cleanup: context_manager
# id: check_english_endpoint_candidate_preserves_corpus_closure
#   proves: english_attachment_source_structure
#   call: self::test_endpoint_candidate_preserves_corpus_closure
#   requires: pytest, pinned_ucns
#   mutates: none
#   cleanup: context_manager
# === END CHECKS ===
# SPDX-License-Identifier: FSL-1.1-ALv2
# Copyright 2026 Erin Spencer
"""Complete-corpus consumer acceptance, with no admission or geometry mocks.

GPT generated; context, prompt Erin Spencer.
Usage: UCHC_STRUCTURAL_FIELD=/path/to/verified/field pytest -c /dev/null
ordinal_tests/test_attachment_corpus.py. Missing corpus is a failure.
"""
import json
import os

import pytest

from english_gonol.attachment_construction import RecursiveStructuralField, authority
from ucns.attachment_codec import replay_graph


@pytest.fixture(scope='module')
def field():
    path = os.environ.get('UCHC_STRUCTURAL_FIELD')
    if not path:
        pytest.fail('UCHC_STRUCTURAL_FIELD must name the complete verified corpus')
    with RecursiveStructuralField(path, bearing='exit-heading-v1') as opened:
        assert opened.complete_corpus
        yield opened


@pytest.mark.parametrize('text', ('word', 'word word', ' word  word ', 'word word.'))
def test_complete_query_retains_source_and_occurrences(field, text):
    word = field.word('word')
    assert word['gonal_order'] == word['attachment_geometry']['graph']
    assert 'attachment' not in word and 'definition_attachment' not in word
    assert word['historical_structural_geometry']['gonal_order'] == 'hmmm:UCNS_OPERATION_REQUIRED'
    query = field.construct(text)
    result = field.geometry(query, operation='recursive-stack')
    assert result['standing'] == 'constructed'
    assert result['source_structure'] == query
    assert result['geometry_authority'] == authority()
    assert result['bearing_standing'] == 'unselected-candidate'
    words = [p for p in query['parts'] if p['kind'] == 'word']
    assert len(result['word_occurrences']) == len(words)
    assert len(result['word_interiors']) == 1
    obj = replay_graph(json.loads(json.dumps(result['word_stack'])))
    assert len(obj.participants) == len(words)
    assert obj.recover() == tuple('word' * len(words))
    assert result['source_structure']['word_sites'] == query['word_sites']
    assert [p['part_ordinal'] for p in result['word_occurrences']] == [p['ordinal'] for p in words]
    sentence = field.compose(query, relation='sentence')
    assert sentence['standing'] == ('logically-closed' if text.endswith('.') else 'refused')


def test_no_policy_is_a_narrow_bearing_boundary(field):
    old = field.bearing
    try:
        field.bearing = None
        result = field.geometry(field.construct('word word'), operation='recursive-stack')
        assert result['standing'] == 'partial'
        assert result['code'] == 'CLOSED_WORD_BEARING_POLICY_REQUIRED'
        assert len(result['word_occurrences']) == 2 and len(result['word_interiors']) == 1
    finally:
        field.bearing = old


def test_endpoint_candidate_preserves_corpus_closure(field):
    old = field.bearing
    try:
        field.bearing = 'root-endpoint-v1'
        query = field.construct('word word.')
        result = field.compose(query, relation='sentence')
        assert result['standing'] == 'logically-closed'
        obj = replay_graph(result['attachment_geometry']['word_stack'])
        assert obj.recover() == tuple('wordword')
    finally:
        field.bearing = old
# ratios: loc_comments=56:27 imports_exports=5:4 calls_definitions=22:4
