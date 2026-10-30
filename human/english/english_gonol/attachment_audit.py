# ratios: loc_comments=65:31 imports_exports=7:2 calls_definitions=31:2
# SPDX-License-Identifier: FSL-1.1-ALv2
# Copyright 2026 Erin Spencer
# === MODULE_BUILD ===
# id: english_attachment_complete_audit
#   module_name: attachment_audit
#   module_kind: verification-tool
#   summary: complete forward word and typed lexical ownership census over a verified corpus
#   owner: Erin Spencer
#   public_surface: audit, main
#   internal_surface: ordered stream digests
#   auth_boundary: verified structural field and pinned native modules
#   storage_boundary: corpus read-only; JSON report to stdout
#   network_boundary: none
#   user_data_boundary: public corpus only
#   admin_only: false
#   tests: complete-corpus execution and source/installed report equality
#   rollout: additive attachment profile evidence
#   rollback: preserve historical structural profile
#   requires: english_recursive_attachment_consumer
#   unresolved: candidate bearing selection and numerical definition attachment
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: english_attachment_complete_census
#   given: a verified complete structural corpus
#   then: every word is reconstructed or explicitly refused and every definition retains its whole lexical owner, constituents and source succession
# === END CONTRACTS ===
"""GPT generated; context, prompt Erin Spencer.

Usage: python -m english_gonol.attachment_audit /path/to/structural-field
This finite complete audit has no sampling or scientific runtime cutoff.
Stream hashes bind ordered results without retaining a second corpus in memory.
"""
import argparse
from collections import Counter
import hashlib
import json

from english_gonol.attachment_construction import RecursiveStructuralField, authority
from english_gonol.ordinal_construction import OrdinalGeometryError
from english_gonol.structural_rules import digest


def audit(path):
    counts, refusals = Counter(), Counter()
    words_hash, definitions_hash = hashlib.sha256(), hashlib.sha256()
    with RecursiveStructuralField(path) as field:
        if not field.complete_corpus:
            raise ValueError('COMPLETE_CORPUS_REQUIRED_FOR_PUBLIC_GONOL')
        for wid, surface in field.db.execute('SELECT id,surface FROM words ORDER BY id'):
            counts['words'] += 1
            try:
                obj = field._closed_word(surface, wid)
            except OrdinalGeometryError as exc:
                if exc.code != 'PUBLIC_GONOL_ANGLE_UNAVAILABLE':
                    raise
                counts['refused_words'] += 1
                refusals.update(exc.glyphs)
                record = {'word_id': wid, 'surface': surface, 'code': exc.code, 'glyphs': list(exc.glyphs)}
            else:
                assert obj.recover() == tuple(surface)
                assert [obj.depth(i) for i in range(len(surface))] == list(range(len(surface), 0, -1))
                counts['constructed_words'] += 1
                record = {'word_id': wid, 'construction': obj.record()}
            words_hash.update((digest(record) + '\n').encode())
        for rid, text, owner, ordinal, previous, provenance, old_state in field.db.execute(
                "SELECT id,text,owner_record_id,ordinal,previous_definition_id,provenance,origin_state FROM records WHERE kind='definition' ORDER BY id"):
            result = field.definition(rid)
            lexical = result['lexical_owner']
            assert lexical['record_id'] == owner and lexical['kind'] == 'lexical-construction'
            assert result['text'] == text and result['provenance'] == json.loads(provenance)
            assert result['definition_succession'] == {'ordinal': ordinal, 'previous': previous}
            for source_id, source_text, parts in ((rid, text, result['parts']), (owner, lexical['text'], lexical['parts'])):
                source_parts = list(field.db.execute(
                    'SELECT ordinal,kind,word_id,character_id,start_offset,end_offset,function FROM components WHERE record_id=? ORDER BY ordinal', (source_id,)))
                assert len(source_parts) == len(parts)
                for part, row in zip(parts, source_parts):
                    n, kind, wid, cid, start, end, function = row
                    assert part == {'ordinal': n, 'kind': kind, 'identity': wid if kind == 'word' else cid,
                                    'start': start, 'end': end, 'function': json.loads(function)}
                assert ''.join(source_text[p['start']:p['end']] for p in parts) == source_text
            assert len(result['constituent_direct']) == len(result['parts'])
            assert all(p['owner'] == result['origin'] for p in result['constituent_direct'])
            counts['definitions'] += 1
            counts['formerly_compound_definitions'] += int(old_state == 'hmmm:compound-lexical-origin')
            definitions_hash.update((result['attachment_receipt'] + '\n').encode())
        assert counts['words'] == field.db.execute('SELECT count(*) FROM words').fetchone()[0]
        result = {'schema': 'english.attachment-corpus-audit.v1', 'geometry_authority': authority(),
                  'field_receipt': field._field_receipt, 'counts': dict(counts),
                  'unplaced_glyph_word_counts': dict(sorted(refusals.items())),
                  'word_stream_sha256': words_hash.hexdigest(), 'definition_stream_sha256': definitions_hash.hexdigest(),
                  'scope': 'all corpus words and all definition ownership overlays; no bearing candidate selected',
                  'hmmm': ['Numerical definition attachment and bearing selection remain open.']}
        return {**result, 'receipt': digest(result)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('field')
    args = parser.parse_args()
    print(json.dumps(audit(args.field), sort_keys=True, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
# ratios: loc_comments=65:31 imports_exports=7:2 calls_definitions=31:2
