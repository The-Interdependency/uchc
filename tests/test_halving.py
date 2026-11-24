# ratios: loc_comments=150:1 imports_exports=13:11 calls_definitions=91:12
"""Run pytest tests/test_halving.py with the pinned producer installed or UCHC_HALVING_UCNS_ROOT set."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from fractions import Fraction
import json
import os
from pathlib import Path

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
    from english_gonol.unicode_construction import additive_resultant, construct_text
    from uchc_halving.cli import main
    opts = options()
    assert construct_text is h.construct_text
    assert additive_resultant is h.additive_resultant
    args = ['bull']
    if opts['ucns_source_root']:
        args.extend(['--ucns-source-root', opts['ucns_source_root']])
    main(args)
    output = json.loads(capsys.readouterr().out)
    assert output['radii'] == [[1,16],[1,8],[1,4],[1,2]]
    word = construct_text('bull', **opts)
    assert output['closed']['vectors'] == {
        'placement_endpoint': h.resultant(word, **opts).record(),
        'additive_resultant': additive_resultant(word, **opts).record(),
    }


def test_boundaries_and_additive_sum_on_one_epicycle():
    opts = options()
    text = 'ABCDEFGHIJ'
    expected_sum = h.additive_resultant(h.construct_text(text, **opts), **opts)
    words = {(i, j): h.construct_text(text[i:j], **opts)
             for i in range(len(text)) for j in range(i + 1, len(text) + 1)}
    for mask in range(1 << (len(text) - 1)):
        breaks = [i for i in range(1, len(text)) if mask & (1 << (i - 1))]
        cuts = [0, *breaks, len(text)]
        group = h.construct_sequence(tuple(words[i, j] for i, j in zip(cuts, cuts[1:])), **opts)
        glyph_lengths = [ray.radius for part in group.participants for ray in part.interior.rays]
        decoded = [i for i in range(1, len(glyph_lengths)) if glyph_lengths[i] <= glyph_lengths[i - 1]]
        assert decoded == breaks
        assert group.additive_resultant == expected_sum


def test_local_frame_radius_survives_a_collision_of_raw_lengths():
    opts = options()
    single = h.construct_sequence((h.construct_text('AB', **opts),), **opts)
    two = h.construct_sequence((h.construct_text('A', placement_radius=Fraction(1, 2), **opts),
                                h.construct_text('B', **opts)), **opts)

    def lengths(group):
        root = h.replay_closed(h.closed_record(group, **opts), **opts)
        return [(r.radius, child.interior.radius) for child in root.participants for r in child.interior.rays]

    first, second = lengths(single), lengths(two)
    assert [r for r, _ in first] == [r for r, _ in second] == [Fraction(1, 4), Fraction(1, 2)]
    assert [r / frame for r, frame in first] == [Fraction(1, 4), Fraction(1, 2)]
    assert [r / frame for r, frame in second] == [Fraction(1, 2), Fraction(1, 2)]


def test_cancelled_sum_survives_replay_and_reentry():
    opts = options()
    word = h.construct_text(' ' + chr(0x88020), **opts)
    assert word.additive_resultant.terms == ()
    assert h.resultant(word, **opts).terms
    east = h.construct_text(' ', placement_radius=3, **opts)
    phrase = h.construct_sequence((word, east, east), placement_radius=5, **opts)
    packet = json.loads(json.dumps(h.closed_record(phrase, **opts)))
    replayed = h.replay_closed(packet, **opts)
    assert replayed.participants[0].interior.additive_resultant.terms == ()
    assert replayed.participants[1].interior is replayed.participants[2].interior
    assert replayed.additive_resultant == east.additive_resultant.scaled(10)
    next_scale = h.construct_sequence((replayed, replayed), **opts)
    assert next_scale.additive_resultant == phrase.additive_resultant.scaled(2)
    for field in ('placement_endpoint', 'additive_resultant'):
        damaged = deepcopy(packet)
        damaged['vectors'][field] = []
        with pytest.raises(ValueError, match='VECTOR_MISMATCH'):
            h.replay_closed(damaged, **opts)
    alias = deepcopy(packet)
    alias['vectors']['additive_resultant'][0]['coefficient'][1] = True
    with pytest.raises(ValueError, match='VECTOR_MISMATCH'):
        h.replay_closed(alias, **opts)


def test_original_v1_record_replays_with_both_results():
    opts = options()
    packet = json.loads(Path(__file__).with_name('ordinal-halving-v1-record.json').read_text(encoding='utf-8'))
    root = h.replay_closed(packet, **opts)
    assert root.receipt == '351f4d886fd7205c253f33e1259f8011bdcedbb91d232b26dc76ae0440f90184'
    assert root.participants[0].interior is root.participants[1].interior
    assert root.additive_resultant == h.construct_text('AëAë', **opts).additive_resultant
    new = h.closed_record(root, **opts)
    assert new['graph'] == packet['graph'] and new['record_version'] == 2
    assert h.replay_closed(new, **opts).rays == root.rays
    del new['vectors'], new['record_version']
    with pytest.raises(ValueError, match='PROVENANCE'):
        h.replay_closed(new, **opts)


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
# ratios: loc_comments=150:1 imports_exports=13:11 calls_definitions=91:12
