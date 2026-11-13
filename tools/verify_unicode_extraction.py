# ratios: loc_comments=56:32 imports_exports=7:1 calls_definitions=27:1
# === MODULE_BUILD ===
# id: uchc_unicode_extraction_verifier
#   module_name: verify_unicode_extraction
#   module_kind: verification-tool
#   summary: verify exact Stack Unicode extraction and recursive installed-package replay
#   owner: Erin Spencer
#   public_surface: command line
#   internal_surface: exact source, graph, module and native-object checks
#   auth_boundary: integrity only; no producer authentication
#   storage_boundary: reads explicit source checkouts and extraction records
#   network_boundary: none
#   user_data_boundary: synthetic local fixture only
#   admin_only: false
#   tests: tests/test_unicode_verification.py, .github/workflows/unicode-recursive.yml
#   rollout: source and clean installed package must emit the same verification record
#   rollback: retain historical candidate records; revert source and extraction pin together
#   requires: exact Stack source and explicit UCNS source checkout
#   unresolved: stable publication and domain graduation
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: uchc_unicode_exact_extraction
#   given: an exact Stack checkout, an explicit native producer and the extracted package
#   then: require matching committed, copied and imported source bytes and replay a completed Unicode object recursively
# id: uchc_unicode_verification_not_optimized
#   given: optimized Python disables verification assertions
#   then: refuse before emitting an extraction claim
# === END CONTRACTS ===
"""GPT generated; context, prompt Erin Spencer.

Run with source PYTHONPATH or isolated installed Python:
python tools/verify_unicode_extraction.py /path/to/stack --ucns-source-root /path/to/ucns
The resulting records must match byte for byte. No corpus or graduation claim.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess

from english_gonol import unicode_construction as consumer


def main():
    if not __debug__:
        raise SystemExit('OPTIMIZED_VERIFICATION_FORBIDDEN')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('forge', type=Path)
    parser.add_argument('--ucns-source-root', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    graph = json.loads((root / 'docs/work-graphs/unicode-recursive-v1.json').read_text())
    extraction = json.loads((root / 'human/english/experiments/unicode-recursive-v1/extraction.json').read_text())
    payload = {key: graph[key] for key in ('repositories', 'boundaries')}
    assert graph['work_graph_sha256'] == hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert all(graph['boundaries'][key] is False for key in ('authority_transfer', 'proof_status_transfer', 'measurement_status_transfer'))
    sources = {row['repository']: row['commit'] for row in graph['repositories']}
    source = sources['The-Interdependency/stack']
    assert subprocess.check_output(['git', '-C', str(args.forge), 'rev-parse', 'HEAD'], text=True).strip() == source
    assert extraction['source_commit'] == source and extraction['authority_transfer'] is False
    assert extraction['work_graph_sha256'] == graph['work_graph_sha256']
    assert extraction['geometry_authority'] == consumer.authority()
    assert consumer.UCNS_COMMIT == sources['The-Interdependency/ucns']
    expected = {'human/english/english_gonol/unicode_construction.py': 'english_gonol/unicode_construction.py',
                'tests/test_unicode_recursive.py': 'unicode_tests/test_unicode_recursive.py'}
    assert len(extraction['files']) == len(expected)
    assert {item['target']: item['source'] for item in extraction['files']} == expected
    for item in extraction['files']:
        original = args.forge / 'research/english-gonol' / item['source']
        committed = subprocess.check_output(['git', '-C', str(args.forge), 'show', source + ':research/english-gonol/' + item['source']])
        copied = root / item['target']
        assert committed == original.read_bytes() == copied.read_bytes(), item['source']
        assert hashlib.sha256(committed).hexdigest() == item['sha256']
        if item['source'].startswith('english_gonol/'):
            assert Path(consumer.__file__).read_bytes() == committed
    text = 'Aë e\u0308!\n\x00'
    leaf = consumer.construct_text(text, ucns_source_root=args.ucns_source_root)
    first = consumer.construct_sequence((leaf, leaf), bearings=(0, Fraction(1, 2)),
                                        source='extraction:first', ucns_source_root=args.ucns_source_root)
    record = consumer.closed_record(first, ucns_source_root=args.ucns_source_root)
    replay = consumer.replay_closed(json.loads(json.dumps(record)), ucns_source_root=args.ucns_source_root)
    parent = consumer.construct_sequence((replay, replay), bearings=(0, Fraction(1, 2)),
                                         source='extraction:parent', ucns_source_root=args.ucns_source_root)
    assert parent.recover() == text * 4
    assert parent.utf32_be == (text * 4).encode('utf-32-be')
    assert parent.participants[0] is replay and parent.participants[1] is replay
    print(json.dumps({'source_commit': source, 'files': len(expected),
                      'work_graph_sha256': graph['work_graph_sha256'],
                      'geometry_authority': consumer.authority(),
                      'recursive_receipt': parent.receipt, 'standing': 'exact extraction and recursive replay'}, sort_keys=True))


if __name__ == '__main__':
    main()
# ratios: loc_comments=56:32 imports_exports=7:1 calls_definitions=27:1
