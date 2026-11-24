# ratios: loc_comments=80:1 imports_exports=12:7 calls_definitions=48:7
"""Run pytest tests/test_halving.py with the pinned producer installed or UCHC_HALVING_UCNS_ROOT set."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from fractions import Fraction
import json
import os

import pytest
import uchc_halving as h


def options():
    return {'ucns_source_root': os.environ.get('UCHC_HALVING_UCNS_ROOT')}


def test_append_repeated_glyphs_and_order():
    opts = options()
    prefix = h.construct_text('bul', **opts)
    word = h.construct_text('bull', **opts)
    assert [r.radius for r in word.rays] == [Fraction(1, n) for n in (16, 8, 4, 2)]
    assert [r.radius / 2 for r in prefix.rays] == [r.radius for r in word.rays[:-1]]
    assert word.participants[2].turn == word.participants[3].turn
    assert word.depth(2) == 2 and word.depth(3) == 1
    assert h.resultant(h.construct_text('AB', **opts), **opts) != h.resultant(h.construct_text('BA', **opts), **opts)


def test_parent_scale_retains_interiors_and_full_scalar_views():
    opts = options()
    text = 'ëe\u0308 \x00𐍈'
    child = h.construct_text(text, source='fixture:one', placement_radius=3, **opts)
    tree = h.construct_sequence((child, child), placement_radius=5, **opts)
    assert [r.radius for r in tree.rays] == [Fraction(5, 4), Fraction(5, 2)]
    packet = json.loads(json.dumps(h.closed_record(tree, **opts)))
    assert all('bit_radius' not in node['construction'] for node in packet['graph']['nodes'])
    restored = h.replay_closed(packet, **opts)
    first, second = (p.interior for p in restored.participants)
    assert first is second and first.receipt == child.receipt
    assert first.rays == child.rays and first.rays[-1].radius == Fraction(3, 2)
    text_again = ''.join(restored.recover())
    assert text_again.encode('utf-8') == (text * 2).encode('utf-8')
    assert first.participants[0].turn != first.participants[1].turn
    grandparent = h.construct_sequence((restored, child), **opts)
    assert ''.join(grandparent.recover()) == text * 3
    packet['graph']['nodes'][0]['construction']['participants'].reverse()
    with pytest.raises(ValueError):
        h.replay_closed(packet, **opts)


def test_reject_foreign_profile_and_invalid_scalar():
    opts = options()
    word = h.construct_text('A', **opts)
    packet = deepcopy(h.closed_record(word, **opts))
    packet['profile'] = 'uchc.unicode-recursive/2'
    with pytest.raises(ValueError, match='PROVENANCE'):
        h.replay_closed(packet, **opts)
    with pytest.raises(ValueError):
        h.construct_text('\ud800', **opts)
    with pytest.raises(ValueError):
        h.construct_text('word', placement_radius=0, **opts)


def test_concurrent_constructors_share_native_classes():
    opts = options()
    with ThreadPoolExecutor(4) as pool:
        words = tuple(pool.map(lambda c: h.construct_text(c, **opts), 'ABCD'))
    assert ''.join(h.construct_sequence(words, **opts).recover()) == 'ABCD'


def test_previous_text_import_and_cli(capsys):
    from english_gonol.unicode_construction import construct_text
    from uchc_halving.cli import main
    opts = options()
    assert construct_text is h.construct_text
    args = ['bull']
    if opts['ucns_source_root']:
        args.extend(['--ucns-source-root', opts['ucns_source_root']])
    main(args)
    assert json.loads(capsys.readouterr().out)['radii'] == [[1,16],[1,8],[1,4],[1,2]]


def test_halving_runs_without_the_encoding_module_and_rejects_source_drift(tmp_path):
    from importlib.metadata import distribution
    from pathlib import Path
    from shutil import copyfile

    root = options()['ucns_source_root']
    source = Path(root) / 'src/ucns' if root else Path(distribution('ucns').locate_file('ucns'))
    target = tmp_path / 'src/ucns'
    target.mkdir(parents=True)
    for name in ('ordinal_affixiation', 'scalar_bearing', 'attachment_stack', 'attachment_codec'):
        copyfile(source / (name + '.py'), target / (name + '.py'))
    assert not (target / 'unicode_gonol.py').exists()
    assert ''.join(h.construct_text('ë', ucns_source_root=tmp_path).recover()) == 'ë'
    producer = target / 'scalar_bearing.py'
    producer.write_bytes(producer.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='DRIFT'):
        h.construct_text('ë', ucns_source_root=tmp_path)
# ratios: loc_comments=80:1 imports_exports=12:7 calls_definitions=48:7
