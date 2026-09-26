# ratios: loc_comments=148:22 imports_exports=12:2 calls_definitions=70:5
"""Exhaust the pinned corpus through the installed UCHC input contract.

Usage: python tools/verify_inference_corpus.py --database /data/construct.db
 --database-sha256 SHA256 --logical-receipt SHA256 --output receipt.json
No sampling, network or neural inference. A failing assertion exits nonzero.
"""
# === MODULE_BUILD ===
# id: uchc_verify_inference_corpus
#   module_name: verify_inference_corpus
#   module_kind: instrument
#   summary: exhaustively compares native reader outputs with all pinned source rows
#   owner: Erin Spencer
#   public_surface: verify, main
#   internal_surface: independent SQLite row comparison
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: CI complete pinned English corpus
#   rollout: release candidate acceptance; not a neural readiness gate
#   rollback: retain failed receipt evidence and withhold release
# === END MODULE_BUILD ===
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
from itertools import groupby, zip_longest
import json
from pathlib import Path
import platform
import sqlite3
import time

from english_gonol import inference_input, hyperspace_construct
from english_gonol.inference_input import EnglishConstruct

PINNED_LOGICAL = '12277b4959c0c72b7af12097b8a77bf91866bbf669e7f4ac07b6a5f1426ebb57'
EXPECTED = {'characters': 118, 'words': 164864, 'word_characters': 1739949,
            'definitions': 185155, 'definition_components': 3535375,
            'semantic_evidence': 866183, 'unresolved_semantic_evidence': 0}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _groups(db: sqlite3.Connection, table: str, fields: str):
    query = (f'SELECT e.definition_id, {fields} FROM {table} e '
             'JOIN definitions d ON e.definition_id=d.id '
             'ORDER BY d.origin_word_id, d.ordinal, e.id')
    return iter((key, tuple(row[1:] for row in rows))
                for key, rows in groupby(db.execute(query), key=lambda row: row[0]))


def verify(database: Path, database_sha256: str, logical_receipt: str) -> dict:
    _require(logical_receipt == PINNED_LOGICAL, 'not the complete pinned English corpus')
    started = time.monotonic()
    observed = {name: 0 for name in EXPECTED}
    definition_digest = hashlib.sha256()
    word_digest = hashlib.sha256()
    with EnglishConstruct(database, database_sha256=database_sha256,
                          logical_receipt=logical_receipt) as corpus:
        db = sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)
        try:
            scalars = dict(db.execute('SELECT id, scalar FROM characters'))
            observed['characters'] = len(scalars)
            _require(len(corpus.inventory) == len(scalars), 'glyph inventory scope drift')
            full_glyph_text = ''.join(scalars.values())
            frame = corpus.resolve_text(full_glyph_text, source_id='corpus:all-glyphs')
            _require(frame.glyphs_admitted, 'an admitted corpus glyph was lost')
            _require(frame.recover_utf8() == full_glyph_text.encode(), 'glyph recovery failed')
            _require(corpus.replay(frame.to_bytes()) == frame, 'glyph frame replay failed')
            words = {}
            expected_words = db.execute('SELECT id, surface FROM words ORDER BY id')
            for record, row in zip_longest(corpus.iter_words(), expected_words):
                _require(record is not None and row is not None, 'word enumeration incomplete')
                native = record.gonol
                _require((native.word_id, native.surface) == row, 'word identity changed')
                _require(''.join(scalars[i] for i in native.glyph_ids) == native.surface,
                         'word glyph construction lost order/multiplicity')
                words[native.word_id] = native.surface
                word_digest.update(json.dumps(asdict(record), sort_keys=True,
                                   ensure_ascii=False).encode())
                observed['words'] += 1
                observed['word_characters'] += len(native.glyph_ids)
            resolved = _groups(db, 'semantic_evidence',
                               'e.id, e.source_ordinal, e.channel, e.relation, e.target_word_id, e.target_ref')
            unresolved = _groups(db, 'unresolved_semantic_evidence',
                                 'e.id, e.source_ordinal, e.channel, e.relation, e.target_ref')
            next_resolved = next(resolved, None)
            next_unresolved = next(unresolved, None)
            rows = db.execute('SELECT id, origin_word_id, part_of_speech, ordinal, '
                'sense_id, synset_id, definition_index, text, previous_definition_id '
                'FROM definitions ORDER BY origin_word_id, ordinal')
            previous = {}
            for record, row in zip_longest(corpus.iter_definitions(), rows):
                _require(record is not None and row is not None, 'definition enumeration incomplete')
                native = record.gonol
                actual = (native.definition_id, native.origin_word_id, record.part_of_speech,
                          native.ordinal, record.sense_id, record.synset_id,
                          record.definition_index, record.text, record.previous_definition_id)
                _require(actual == row, 'definition identity/provenance changed')
                _require(native.origin_word_id in words, 'missing word origin')
                _require(record.previous_definition_id == previous.get(native.origin_word_id),
                         'definition predecessor changed')
                previous[native.origin_word_id] = native.definition_id
                _require(tuple((c.kind, c.identity_id) for c in record.components) == native.constituent_ids,
                         'definition native construction and components disagree')
                parts = []; end = 0
                for component in record.components:
                    _require(component.start == end, 'definition components are not contiguous')
                    part = (words[component.identity_id] if component.kind == 'word'
                            else scalars[component.identity_id])
                    _require(record.text[component.start:component.end] == part,
                             'component source span or identity changed')
                    parts.append(part); end = component.end
                _require(''.join(parts) == record.text, 'definition does not recover completely')
                expected_evidence = []
                if next_resolved is not None and next_resolved[0] == native.definition_id:
                    expected_evidence.extend(('resolved', *values) for values in next_resolved[1])
                    next_resolved = next(resolved, None)
                if next_unresolved is not None and next_unresolved[0] == native.definition_id:
                    expected_evidence.extend(('unresolved', *values[:4], None, values[4])
                                             for values in next_unresolved[1])
                    next_unresolved = next(unresolved, None)
                actual_evidence = [(e.status, e.evidence_id, e.source_ordinal, e.channel,
                                    e.relation, e.target_word_id, e.target_ref) for e in record.evidence]
                _require(actual_evidence == expected_evidence, 'semantic source evidence changed')
                for evidence in record.evidence:
                    key = ('semantic_evidence' if evidence.status == 'resolved'
                           else 'unresolved_semantic_evidence')
                    observed[key] += 1
                    _require(evidence.target_word_id is None or evidence.target_word_id in words,
                             'semantic target not recoverable')
                observed['definitions'] += 1
                observed['definition_components'] += len(record.components)
                definition_digest.update(json.dumps(asdict(record), sort_keys=True,
                                         ensure_ascii=False).encode())
            _require(next_resolved is None and next_unresolved is None,
                     'unconsumed semantic evidence')
            _require(observed == EXPECTED, f'incomplete scope: {observed}')
            identity = asdict(corpus.identity)
        finally:
            db.close()
    _require(_sha(database) == database_sha256, 'source database was modified')
    result = {
        'schema': 'uchc.english.inference-input-acceptance', 'version': '1.0.0',
        'standing': 'SURVIVED', 'scope': 'complete pinned English construct; no sample',
        'construct': identity, 'counts': observed,
        'word_records_sha256': word_digest.hexdigest(),
        'definition_records_sha256': definition_digest.hexdigest(),
        'reader_source_sha256': _sha(Path(inference_input.__file__)),
        'native_producer_sha256': _sha(Path(hyperspace_construct.__file__)),
        'python': platform.python_version(),
        'hmmm': ['neural architecture, learning, propagation, readout and usefulness are not established by input acceptance'],
    }
    result['receipt_sha256'] = hashlib.sha256(json.dumps(result, sort_keys=True,
        ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    result['resources'] = {'elapsed_seconds': time.monotonic() - started}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--database-sha256', required=True)
    parser.add_argument('--logical-receipt', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.database, args.database_sha256, args.logical_receipt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
# ratios: loc_comments=148:22 imports_exports=12:2 calls_definitions=70:5
