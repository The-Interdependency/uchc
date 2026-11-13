# ratios: loc_comments=88:30 imports_exports=9:5 calls_definitions=52:7
# === CHECKS ===
# id: uchc_unicode_recursive_completion_check
#   proves: uchc_unicode_recursive_completion
#   call: self::test_unicode_objects_reenter_after_replay
#   requires: python3, pytest, pinned_ucns
#   timeout: 60
#   mutates: none
#   cleanup: none
# id: uchc_unicode_recursive_refusal_check
#   proves: uchc_unicode_recursive_completion
#   call: self::test_object_and_provenance_refusals
#   requires: python3, pytest, pinned_ucns
#   timeout: 60
#   mutates: none
#   cleanup: none
# id: uchc_unicode_complete_source_closure_check
#   proves: uchc_unicode_native_integrity
#   call: self::test_complete_source_closure_is_checked_before_execution
#   requires: python3, pytest, pinned_ucns
#   timeout: 60
#   mutates: filesystem
#   cleanup: tmp_path
# id: uchc_unicode_concurrent_reentry_check
#   proves: uchc_unicode_recursive_completion, uchc_unicode_native_integrity
#   call: self::test_concurrent_first_use_objects_can_be_reused
#   requires: python3, pytest, pinned_ucns
#   timeout: 60
#   mutates: in-process native loader cache
#   cleanup: thread_pool_exit
# === END CHECKS ===
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from fractions import Fraction
import json
import os
from pathlib import Path
from threading import Barrier

import pytest

from english_gonol import unicode_construction as consumer


@pytest.fixture
def native_root():
    return Path(os.environ['UCHC_UNICODE_UCNS_ROOT'])


def test_unicode_objects_reenter_after_replay(native_root):
    text = '\ufeffAë𐍈 e\u0308!\n\x00'
    word = consumer.construct_text(text, ucns_source_root=native_root, placement_radius=7)
    original = word.record()
    sequence = consumer.construct_sequence((word, word), bearings=(0, Fraction(1, 2)),
                                           ucns_source_root=native_root, source='fixture:sequence',
                                           placement_radius=3)
    parent = consumer.construct_sequence((sequence, word, sequence),
                                         bearings=(0, Fraction(1, 3), Fraction(2, 3)),
                                         ucns_source_root=native_root, source='fixture:parent',
                                         placement_radius=11)
    assert parent.recover() == text * 5
    assert parent.utf32_be == (text * 5).encode('utf-32-be')
    assert parent.utf8 == (text * 5).encode('utf-8')
    assert parent.participants[0] is sequence and parent.participants[2] is sequence
    assert sequence.participants[0] is word and sequence.participants[1] is word
    assert word.record() == original
    assert {p.radius for p in parent.placements} == {11}
    assert {p.radius for p in sequence.placements} == {3}
    assert {p.radius for p in word.placements} == {7}
    packet = consumer.closed_record(parent, ucns_source_root=native_root)
    restored = consumer.replay_closed(json.loads(json.dumps(packet)), ucns_source_root=native_root)
    assert restored.receipt == parent.receipt
    assert restored.participants[0] is restored.participants[2]
    final = consumer.construct_sequence((restored,), bearings=(Fraction(1, 7),),
                                        ucns_source_root=native_root, source='fixture:final')
    assert final.recover() == text * 5
    glyphs = tuple(consumer.construct_glyph(c, ucns_source_root=native_root) for c in 'eë')
    leaf = consumer.construct_sequence(glyphs, ucns_source_root=native_root, source='fixture:glyphs')
    assert leaf.recover() == 'eë'
    assert leaf.bearings == tuple(g.turn for g in glyphs)


def test_object_and_provenance_refusals(native_root):
    word = consumer.construct_text('ab', ucns_source_root=native_root)
    with pytest.raises(ValueError, match='CLOSED_OBJECT_BEARINGS_REQUIRED'):
        consumer.construct_sequence((word,), ucns_source_root=native_root)
    with pytest.raises(TypeError, match='NATIVE_UNICODE_OBJECT_REQUIRED'):
        consumer.construct_sequence(('ab',), bearings=(0,), ucns_source_root=native_root)
    parent = consumer.construct_sequence((word,), bearings=(0,), ucns_source_root=native_root)
    record = consumer.closed_record(parent, ucns_source_root=native_root)
    for mutate in (
        lambda r: r['geometry_authority'].update(commit='0' * 40),
        lambda r: r['geometry_authority']['source_sha256s'].update({'src/ucns/unicode_recursive.py': '0' * 64}),
        lambda r: r['graph']['nodes'][-1]['object'].update(source='forged'),
        lambda r: r['graph']['nodes'][0]['object']['glyphs'][0].update(utf32_be_bytes=[0, 0, 0, 66]),
    ):
        bad = deepcopy(record)
        mutate(bad)
        with pytest.raises(ValueError):
            consumer.replay_closed(bad, ucns_source_root=native_root)


@pytest.mark.parametrize('name', tuple(consumer.NATIVE_SOURCES))
def test_complete_source_closure_is_checked_before_execution(native_root, tmp_path, monkeypatch, name):
    for module_name in consumer.NATIVE_SOURCES:
        relative = Path('src/ucns') / (module_name + '.py')
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((native_root / relative).read_bytes())
    drift = tmp_path / 'src/ucns' / (name + '.py')
    drift.write_bytes(drift.read_bytes() + b'\nraise RuntimeError("must not execute")\n')
    def forbidden(_sources):
        pytest.fail('native source executed before closure verification')
    monkeypatch.setattr(consumer, '_load_native', forbidden)
    with pytest.raises(ValueError, match='UCNS_UNICODE_PRODUCER_DRIFT'):
        consumer.construct_text('A', ucns_source_root=tmp_path)


def test_concurrent_first_use_objects_can_be_reused(native_root):
    consumer._load_native.cache_clear()
    barrier = Barrier(8)
    def build(_):
        barrier.wait()
        return consumer.construct_text('Aë', ucns_source_root=native_root)
    with ThreadPoolExecutor(max_workers=8) as pool:
        children = tuple(pool.map(build, range(8)))
    parent = consumer.construct_sequence(children, bearings=tuple(Fraction(i, 8) for i in range(8)),
                                         ucns_source_root=native_root)
    assert parent.recover() == 'Aë' * 8
    assert len({type(child) for child in children}) == 1
    assert all(parent.participants[i] is child for i, child in enumerate(children))
# ratios: loc_comments=88:30 imports_exports=9:5 calls_definitions=52:7
