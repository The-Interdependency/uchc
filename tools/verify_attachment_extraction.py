# ratios: loc_comments=50:30 imports_exports=8:1 calls_definitions=25:1
# SPDX-License-Identifier: FSL-1.1-ALv2
# Copyright 2026 Erin Spencer
# === MODULE_BUILD ===
# id: uchc_attachment_extraction_verifier
#   module_name: verify_attachment_extraction
#   module_kind: verification-tool
#   summary: verify exact Stack extraction, graph and imported producer identities
#   owner: Erin Spencer
#   public_surface: command line
#   internal_surface: digest and file comparisons
#   auth_boundary: content integrity; no authentication claim
#   storage_boundary: read-only checkouts
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: source and clean-installed recursive attachment workflow
#   rollout: additive candidate gate
#   rollback: retain historical extraction gates
#   requires: pinned Stack checkout, pinned UCNS installation
#   unresolved: stable publication and graduation
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: uchc_attachment_exact_extraction
#   given: pinned Stack checkout and candidate files
#   then: require complete declared source closure, matching source bytes, graph identity and native producer identity
# === END CONTRACTS ===
"""GPT generated; context, prompt Erin Spencer.

Usage: PYTHONPATH=human/english python tools/verify_attachment_extraction.py /path/to/stack
Run the same command with isolated installed Python to verify packaged modules.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import subprocess

from english_gonol.attachment_construction import authority
from english_gonol.structural_construct import IMPLEMENTATION_FILES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('forge', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    graph = json.loads((root / 'docs/work-graphs/english-recursive-attachment-v1.json').read_text())
    extraction = json.loads((root / 'human/english/experiments/recursive-attachment-v1/extraction.json').read_text())
    payload = {k: graph[k] for k in ('repositories', 'boundaries')}
    assert graph['work_graph_sha256'] == hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert all(graph['boundaries'][k] is False for k in ('authority_transfer', 'proof_status_transfer', 'measurement_status_transfer'))
    source = next(r['commit'] for r in graph['repositories'] if r['repository'] == 'The-Interdependency/stack')
    assert subprocess.check_output(['git', '-C', str(args.forge), 'rev-parse', 'HEAD'], text=True).strip() == source
    assert extraction['source_commit'] == source and extraction['authority_transfer'] is False
    assert extraction['work_graph_sha256'] == graph['work_graph_sha256']
    expected = {'human/english/english_gonol/' + p: 'english_gonol/' + p for p in IMPLEMENTATION_FILES}
    for name in ('ordinal_construction.py', 'attachment_construction.py', 'attachment_audit.py'):
        expected['human/english/english_gonol/' + name] = 'english_gonol/' + name
    for name in ('test_attachment_construction.py', 'test_attachment_corpus.py'):
        expected['tests/' + name] = 'ordinal_tests/' + name
    assert len(extraction['files']) == len(expected)
    assert {item['target']: item['source'] for item in extraction['files']} == expected
    for item in extraction['files']:
        original = args.forge / 'research/english-gonol' / item['source']
        copied = root / item['target']
        committed = subprocess.check_output(['git', '-C', str(args.forge), 'show',
                                             source + ':research/english-gonol/' + item['source']])
        assert original.read_bytes() == committed, item['source']
        assert original.read_bytes() == copied.read_bytes(), item['target']
        assert hashlib.sha256(copied.read_bytes()).hexdigest() == item['sha256']
        if item['source'].startswith('english_gonol/'):
            module = item['source'][:-3].replace('/', '.')
            if module.endswith('.__init__'):
                module = module[:-9]
            installed = Path(importlib.import_module(module).__file__)
            assert installed.read_bytes() == original.read_bytes(), module
    native = next(r for r in graph['repositories'] if r['repository'] == 'The-Interdependency/ucns')
    assert authority()['commit'] == native['commit']
    assert authority() == extraction['geometry_authority']
    print(json.dumps({'standing': 'exact', 'source_commit': source, 'files': len(expected),
                      'work_graph_sha256': graph['work_graph_sha256'], 'geometry_authority': authority()}, sort_keys=True))


if __name__ == '__main__':
    main()
# ratios: loc_comments=50:30 imports_exports=8:1 calls_definitions=25:1
