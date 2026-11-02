# ratios: loc_comments=230:54 imports_exports=9:9 calls_definitions=103:17
# SPDX-License-Identifier: FSL-1.1-ALv2
# Copyright 2026 Erin Spencer
# === MODULE_BUILD ===
# id: english_recursive_attachment_consumer
#   module_name: attachment_construction
#   module_kind: adapter
#   summary: English admission and lexical ownership consuming native recursive UCNS stacks
#   owner: Erin Spencer
#   public_surface: construct_word, construct_sequence, construct_compound, replay_compound, word_record, RecursiveStructuralField, main
#   internal_surface: exact producer integrity and language-only relation records
#   auth_boundary: exact UCNS modules and verified corpus; integrity is not authentication
#   storage_boundary: read-only structural field; caller owns returned records
#   network_boundary: none
#   user_data_boundary: query text remains local
#   admin_only: false
#   tests: ordinal_tests/test_attachment_construction.py, ordinal_tests/test_attachment_corpus.py
#   rollout: explicit recursive-stack profile; historical structural and ordinal replay remain versioned
#   rollback: select historical profile explicitly; never reinterpret an existing receipt
#   requires: ucns_attachment_stack, ucns_attachment_codec, english_structural_profile
#   unresolved: exact closed-word bearing selection, non-Public-Gonol admission and punctuation geometric operations
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: english_attachment_native_authority
#   given: an admitted word or explicitly bound sequence
#   then: all coordinates, headings, halvings, closure and graph replay are produced by exact pinned UCNS modules
# id: english_attachment_source_structure
#   given: a verified query containing repeated words, punctuation and whitespace
#   then: preserve every source part and occurrence and apply the existing admission and sentence-closure gates without splitting or normalizing text
# id: english_attachment_bearing_boundary
#   given: closed words to place at the parent scale
#   then: require an explicit named candidate bearing without reopening the specified recursive stacking operation
# id: english_attachment_lexical_owner
#   given: a definition with a source lexical owner
#   then: the entire closed lexical construction owns the typed definition origin while original parts, succession and provenance remain recoverable
# === END CONTRACTS ===
"""Forward English attachment profile, forged in Stack and extracted into UCHC.

GPT generated; context, prompt Erin Spencer.

Usage::

    python -m english_gonol.attachment_construction word bull
    python -m english_gonol.attachment_construction sequence bull shit --bearing exit-heading-v1
    python -m english_gonol.attachment_construction compound bull shit

The sequence command declares word boundaries explicitly; it does not infer a
sentence. Corpus queries use RecursiveStructuralField and the structural
sentence-closure gate. Both bearing choices are unselected candidates. Every
result retains exact UCNS expressions; display is optional and lossy. Historical
StructuralField and OrdinalStructuralField remain explicit replay interfaces.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import importlib
import json
from pathlib import Path

from english_gonol.ordinal_construction import (
    OrdinalGeometryError, _git_blob_sha1, _ucns,
    construct_glyph_gonol, PUBLIC_GONOL_SHA256,
)
from english_gonol.structural_query import StructuralField
from english_gonol.structural_rules import digest

UCNS_COMMIT = '9cc00771e54336d58ee377faeec87a3a33dbd4bf'
UCNS_BLOBS = {'attachment_stack': '0ce3879257b40d264749c1b65fff23abf186fded', 'attachment_codec': '5e761f8e2169ddb24aa6744a8a577ee4aa4989bd', 'ordinal_affixiation': '9fa84ef20f19fe0c04df680f49b50ea307e6d624', 'public_gonol': 'c1955e46e2dc918fb657cb346e42106d71937e91'}


@lru_cache(maxsize=1)
def _native():
    _ucns()
    modules = {}
    for name, expected in UCNS_BLOBS.items():
        try:
            module = importlib.import_module('ucns.' + name)
        except ImportError as exc:
            raise OrdinalGeometryError('UCNS_ATTACHMENT_PRODUCER_REQUIRED') from exc
        path = getattr(module, '__file__', None)
        try:
            content = Path(path).read_bytes() if path else None
        except OSError as exc:
            raise OrdinalGeometryError('UCNS_ATTACHMENT_PRODUCER_REQUIRED') from exc
        if content is None or _git_blob_sha1(content) != expected:
            raise OrdinalGeometryError('UCNS_ATTACHMENT_PRODUCER_DRIFT')
        modules[name] = module
    if set(modules) != {'attachment_stack', 'attachment_codec', 'ordinal_affixiation', 'public_gonol'}:
        raise OrdinalGeometryError('UCNS_ATTACHMENT_PRODUCER_REQUIRED')
    return modules['attachment_stack'], modules['attachment_codec']


def authority():
    _native()
    return {'repository': 'The-Interdependency/ucns', 'commit': UCNS_COMMIT,
            'source_blobs': dict(UCNS_BLOBS), 'public_gonol_sha256': PUBLIC_GONOL_SHA256}


def construct_word(text, *, source='english.attachment/1:declared-word'):
    """Construct one declared word; no corpus admission is implied by this API."""
    native, _codec = _native()
    admitted = construct_glyph_gonol(text, source=source)
    return native.stack(text, admitted.participants, relation='english.attachment/1:glyph-stack', source=source)


def word_record(word):
    native, codec = _native()
    if not isinstance(word, native.DiskStack):
        raise OrdinalGeometryError('NATIVE_WORD_STACK_REQUIRED')
    expected = construct_word(word.identity, source=word.source)
    if expected.receipt != word.receipt:
        raise OrdinalGeometryError('PUBLIC_GONOL_WORD_STACK_REQUIRED')
    return {'schema': 'english.attachment-word.v1', 'geometry_authority': authority(),
            'graph': codec.export_graph(word), 'recovered_glyphs': list(word.recover()),
            'disk_depths': [word.depth(i) for i in range(len(word.rays))]}


def construct_sequence(words, *, bearing=None, source='english.attachment/1:declared-sequence'):
    """Same native stack, now consuming already closed words; never text.split()."""
    native, _codec = _native()
    if bearing not in native.POLICIES:
        raise OrdinalGeometryError('CLOSED_WORD_BEARING_POLICY_REQUIRED')
    if not isinstance(words, tuple) or not words:
        raise OrdinalGeometryError('CLOSED_WORD_PARTICIPANTS_REQUIRED')
    for word in words:
        closed_record(word)
    return native.stack('declared-word-sequence', tuple(native.Closed(w, bearing) for w in words),
                        relation='english.attachment/1:word-stack', source=source)


def construct_compound(left, right, *, source='english.attachment/1:declared-compound'):
    """Explicit component boundary; the terminal occurrence supplies attachment."""
    if not isinstance(source, str) or not source:
        raise OrdinalGeometryError('SOURCE_IDENTITY_REQUIRED')
    native, codec = _native()
    left_record, right_record = closed_record(left), closed_record(right)
    site = len(left.rays) - 1
    rows = native.attach(left, site, right)
    obj = native.join(left.identity + right.identity, left, right,
                      relation='english.attachment/1:declared-compound', source=source)
    result = {'schema': 'english.attachment-compound.v1', 'source': source,
              'relation': 'declared-compound', 'geometry_authority': authority(),
              'components': [left_record, right_record], 'attachment_ordinal': site,
              'graph': codec.export_graph(obj),
              'incoming_rows': [{'origin': o.record(), 'point': p.record()} for o, p in rows],
              'local_radii_preserved': True, 'definition_owner': 'whole-closed-lexical-construction'}
    return {**result, 'receipt': digest(result)}


def closed_record(obj):
    """Validate either a glyph-built word or a retained explicit compound."""
    native, codec = _native()
    if not isinstance(obj, native.AttachmentJoin):
        return word_record(obj)
    pending, seen = [obj], set()
    while pending:
        current = pending.pop()
        if current.receipt in seen:
            continue
        seen.add(current.receipt)
        if isinstance(current, native.AttachmentJoin):
            expected = native.join(current.left.identity + current.right.identity,
                                   current.left, current.right,
                                   relation='english.attachment/1:declared-compound', source=current.source)
            if current.receipt != expected.receipt:
                raise OrdinalGeometryError('DECLARED_COMPOUND_REQUIRED')
            pending.extend((current.right, current.left))
        else:
            word_record(current)
    return {'schema': 'english.closed-compound.v1', 'geometry_authority': authority(),
            'graph': codec.export_graph(obj)}


def replay_compound(record):
    """Reconstruct both components and the actual attachment, not just a hash."""
    _native_module, codec = _native()
    try:
        if not isinstance(record, dict) or len(record['components']) != 2:
            raise ValueError('two components required')
        left, right = (codec.replay_graph(p['graph']) for p in record['components'])
        expected = construct_compound(left, right, source=record['source'])
        if digest(expected) != digest(record):
            raise ValueError('compound replay mismatch')
        return expected
    except (KeyError, TypeError, ValueError) as exc:
        raise OrdinalGeometryError('COMPOUND_REPLAY_MISMATCH') from exc


class RecursiveStructuralField(StructuralField):
    """Verified corpus adapter. Candidate bearings are explicit per field instance."""

    def __init__(self, out_dir, *, bearing=None):
        native, _codec = _native()
        if bearing is not None and bearing not in native.POLICIES:
            raise OrdinalGeometryError('CLOSED_WORD_BEARING_POLICY_REQUIRED')
        self.bearing = bearing
        super().__init__(out_dir)

    def _closed_word(self, surface, word_id):
        if not self.complete_corpus:
            raise OrdinalGeometryError('COMPLETE_CORPUS_REQUIRED_FOR_PUBLIC_GONOL')
        return construct_word(surface, source='english.structural/1:' + self._field_receipt + ':word:' + str(word_id))

    def word(self, surface):
        result = super().word(surface)
        result['attachment_geometry'] = word_record(self._closed_word(surface, result['word_id']))
        result['historical_structural_geometry'] = {key: result.pop(key) for key in
                                                   ('gonal_order', 'attachment', 'definition_attachment')}
        result['gonal_order'] = result['attachment_geometry']['graph']
        result['geometry_state'] = 'constructed-native-attachment'
        return result

    def geometry(self, record, *, operation):
        if operation != 'recursive-stack':
            return super().geometry(record, operation=operation)
        graph = self.replay(record)
        if not self.complete_corpus:
            return {'standing': 'refused', 'code': 'COMPLETE_CORPUS_REQUIRED_FOR_PUBLIC_GONOL'}
        if graph['refusals']:
            return {'standing': 'refused', 'code': 'PARTICIPANT_ADMISSION_REQUIRED'}
        native, codec = _native()
        words, occurrences, interiors = [], [], {}
        try:
            for part in graph['parts']:
                if part['kind'] != 'word':
                    continue
                surface = graph['source'][part['start']:part['end']]
                word = self._closed_word(surface, part['identity'])
                words.append(word)
                interiors[word.receipt] = word_record(word)
                occurrences.append({'part_ordinal': part['ordinal'], 'start': part['start'],
                                    'end': part['end'], 'word_id': part['identity'], 'interior': word.receipt})
        except OrdinalGeometryError as exc:
            return {'standing': 'refused', 'code': exc.code, 'unplaced_glyphs': list(exc.glyphs)}
        result = {'schema': 'english.recursive-word-placement.v1', 'source_structure': graph,
                  'geometry_authority': authority(), 'word_interiors': list(interiors.values()),
                  'word_occurrences': occurrences, 'scope': 'ordered closed-word placement',
                  'hmmm': ['Punctuation function geometry is not supplied by the word stack.',
                           'Closed-word bearing candidates remain unselected.']}
        if not words:
            return {**result, 'standing': 'refused', 'code': 'CLOSED_WORD_PARTICIPANTS_REQUIRED'}
        if self.bearing is None:
            return {**result, 'standing': 'partial', 'code': 'CLOSED_WORD_BEARING_POLICY_REQUIRED'}
        parent = construct_sequence(tuple(words), bearing=self.bearing,
                                    source='english.query:' + graph['receipt_sha256'])
        result.update(standing='constructed', bearing_policy=self.bearing,
                      bearing_standing='unselected-candidate', word_stack=codec.export_graph(parent))
        result['receipt'] = digest(result)
        return result

    def compose(self, record, *, relation):
        result = super().compose(record, relation=relation)
        if result['standing'] != 'logically-closed':
            return result
        geometry = self.geometry(record, operation='recursive-stack')
        result['attachment_geometry'] = geometry
        result['geometry_state'] = ('constructed-word-stack;candidate-bearing' if geometry['standing'] == 'constructed'
                                    else 'hmmm:' + geometry['code'])
        return result

    def lexical_owner(self, record_id):
        """Whole source lexical closure; this is a typed owner, never a word ID."""
        row = self.db.execute("SELECT text,provenance FROM records WHERE id=? AND kind='lexical'", (record_id,)).fetchone()
        if row is None:
            raise OrdinalGeometryError('LEXICAL_OWNER_REQUIRED')
        parts = []
        for ordinal, kind, wid, cid, start, end, function in self.db.execute(
                'SELECT ordinal,kind,word_id,character_id,start_offset,end_offset,function FROM components WHERE record_id=? ORDER BY ordinal', (record_id,)):
            parts.append({'ordinal': ordinal, 'kind': kind, 'identity': wid if kind == 'word' else cid,
                          'start': start, 'end': end, 'function': json.loads(function)})
        owner = {'schema': 'english.closed-lexical-owner.v1', 'kind': 'lexical-construction',
                 'record_id': record_id, 'field_receipt': self._field_receipt, 'text': row[0],
                 'parts': parts, 'closed': True, 'provenance': json.loads(row[1])}
        return {**owner, 'receipt': digest(owner)}

    def definition(self, record_id):
        result = super().definition(record_id)
        owner = self.lexical_owner(result['owner_record_id'])
        result['historical_origin'] = {'origin': result['origin'], 'state': result['origin_state']}
        result['lexical_owner'] = owner
        result['origin'] = {'space': 'O_D', 'owner_kind': owner['kind'], 'owner_record_id': owner['record_id'],
                            'owner_receipt': owner['receipt']}
        result['origin_state'] = 'whole-closed-lexical-owner'
        result['constituent_direct'] = [{'owner': result['origin'], 'part': i, 'standing': result['origin_state']}
                                       for i in range(len(result['parts']))]
        result['origin_geometry'] = 'hmmm: typed lexical ownership is not a numerical definition attachment'
        result['attachment_profile'] = 'english.attachment/1'
        result['attachment_receipt'] = digest(result)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    word = sub.add_parser('word'); word.add_argument('text')
    sequence = sub.add_parser('sequence'); sequence.add_argument('words', nargs='+')
    sequence.add_argument('--bearing', required=True, choices=('root-endpoint-v1', 'exit-heading-v1'))
    compound = sub.add_parser('compound'); compound.add_argument('left'); compound.add_argument('right')
    args = parser.parse_args()
    try:
        _native_module, codec = _native()
        if args.command == 'word':
            obj = construct_word(args.text)
            result = {**word_record(obj), 'common_view': codec.export_view(obj, kind='common'),
                      'attached_view': codec.export_view(obj)}
        elif args.command == 'sequence':
            obj = construct_sequence(tuple(construct_word(w) for w in args.words), bearing=args.bearing)
            result = {'geometry_authority': authority(), 'bearing_standing': 'unselected-candidate',
                      'bearing_policy': args.bearing, 'graph': codec.export_graph(obj)}
        else:
            result = construct_compound(construct_word(args.left), construct_word(args.right))
    except OrdinalGeometryError as exc:
        print(json.dumps({'standing': 'refused', 'code': exc.code, 'glyphs': exc.glyphs}))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
# ratios: loc_comments=230:54 imports_exports=9:9 calls_definitions=103:17
