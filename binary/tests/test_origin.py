# === CHECKS ===
# id: check_all_256_values_use_byte_axes_not_bit_axes
#   proves: binary_origin_byte_axes
#   call: self::test_all_256_values_use_byte_axes_not_bit_axes
#   mutates: none
#   cleanup: none
#
# id: check_equal_values_preserve_occurrences
#   proves: binary_origin_byte_axes
#   call: self::test_equal_values_preserve_occurrences
#   mutates: none
#   cleanup: none
#
# id: check_repeat_and_residual_closure
#   proves: binary_sequence_closure
#   call: self::test_repeat_and_residual_closure
#   mutates: none
#   cleanup: none
#
# id: check_native_720_return
#   proves: binary_native_geometry
#   call: self::test_native_720_return
#   mutates: none
#   cleanup: none
#
# id: check_space_changes_actual_positions_not_labels
#   proves: binary_native_geometry
#   call: self::test_space_changes_actual_positions_not_labels
#   mutates: none
#   cleanup: none
#
# id: check_recover_from_circle_positions
#   proves: binary_coordinate_recovery, binary_sequence_closure
#   call: self::test_recover_from_circle_positions
#   mutates: none
#   cleanup: none
#
# id: check_all_seven_circles_participate
#   proves: binary_coordinate_recovery, binary_sequence_closure
#   call: self::test_all_seven_circles_participate
#   mutates: none
#   cleanup: none
#
# id: check_round_context_changes_frame_not_message
#   proves: binary_origin_byte_axes
#   call: self::test_round_context_changes_frame_not_message
#   mutates: none
#   cleanup: none
#
# id: check_leading_zero_and_empty_sources
#   proves: binary_sequence_closure
#   call: self::test_leading_zero_and_empty_sources
#   mutates: none
#   cleanup: none
#
# id: check_bad_partitions_refuse
#   proves: binary_source_refusal
#   call: self::test_bad_partitions_refuse
#   mutates: none
#   cleanup: none
#
# id: check_bad_coordinate_counts_gaps_and_frames_refuse
#   proves: binary_source_refusal
#   call: self::test_bad_coordinate_counts_gaps_and_frames_refuse
#   mutates: none
#   cleanup: none
#
# id: check_changed_native_source_refuses_before_execution
#   proves: binary_source_refusal
#   call: self::test_changed_native_source_refuses_before_execution
#   mutates: filesystem
#   cleanup: tempdir_teardown
#
# id: check_work_graph_identity
#   proves: binary_source_refusal
#   call: self::test_work_graph_identity
#   mutates: none
#   cleanup: none
# === END CHECKS ===
"""Run with PYTHONPATH=binary UCNS_ROOT=/checkout/ucns python -m unittest discover -s binary/tests.

The tests execute the pinned native UCNS modules, never fabricated circle classes.
All writes are confined to temporary directories. No network or corpus database.
"""
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from hashlib import sha256
import json
import os
import tempfile
import unittest
from uchc_binary.origin import *

UCNS = Path(os.environ['UCNS_ROOT'])
SPACES = tuple(Fraction(i,9) for i in range(8))


class BinaryOriginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geometry = Geometry(UCNS)

    def fixture(self, data=b'ABxABy'):
        origin = ByteOrigin(data,'native-test',0,self.geometry)
        return close_sequences(origin,(b'AB',b'x',b'y'),(0,1,0,2),(1,2,3),SPACES)

    def replay(self, table, **changes):
        wire = table.wire_occurrences()
        kwargs = dict(scope=table.origin.scope,message_origin=table.origin.message_origin,
            round_id=table.origin.round_id,origin_identity=table.origin.identity,
            byte_length=len(table.origin.source),blocks=tuple(d.data for d in table.definitions),
            circles=tuple(d.occurrences[0].circle for d in table.definitions),spaces=SPACES,
            counts=tuple(sum(o.circle==c for _,o in wire) for c in range(1,8)),
            wire_order=tuple(i for i,_ in wire),
            source_turns=tuple(self.geometry.lift(o.source_state) for _,o in wire))
        kwargs.update(changes)
        return recover_sequences(self.geometry,**kwargs)

    def test_all_256_values_use_byte_axes_not_bit_axes(self):
        origin = ByteOrigin(bytes(range(256)),'all-bytes',0,self.geometry)
        identities = set()
        for i in range(256):
            axis = origin.byte_axis(i)
            self.assertIsInstance(axis,self.geometry.axis_module.AxisCirclePosition)
            self.assertEqual(axis.axis_count,256)
            self.assertEqual(axis.axis_ordinal,i)
            self.assertEqual(axis.turn,Fraction(i,256))
            identities.add(axis.identity_sha256)
        self.assertEqual(len(identities),256)
        with self.assertRaises(BinaryError):
            origin.byte_axis(256)

    def test_equal_values_preserve_occurrences(self):
        origin = ByteOrigin(b'AA','same-byte',0,self.geometry)
        self.assertEqual(len(origin.source),2)
        self.assertNotEqual(origin.byte_axis(0),origin.byte_axis(1))
        table = close_sequences(origin,(b'A',),(0,0),(1,),SPACES)
        self.assertEqual(tuple(o.source_offset for o in table.definitions[0].occurrences),(0,1))

    def test_repeat_and_residual_closure(self):
        table = self.fixture()
        self.assertEqual(table.restore(),b'ABxABy')
        self.assertTrue(table.definitions[0].repeated)
        self.assertFalse(table.definitions[1].repeated)
        self.assertEqual(tuple(o.source_offset for o in table.definitions[0].occurrences),(0,3))
        self.assertEqual(table.definitions[1].attachment_axis.turn,Fraction(1,3))

    def test_native_720_return(self):
        table = self.fixture()
        state = table.definitions[0].state
        self.assertIsInstance(state,self.geometry.mobius_module.NativeMobiusState)
        self.assertNotEqual(state.advance(1).complete_key,state.complete_key)
        self.assertEqual(state.advance(1).visible_key,state.visible_key)
        self.assertEqual(state.advance(2).complete_key,state.complete_key)

    def test_space_changes_actual_positions_not_labels(self):
        table = self.fixture()
        origin = table.origin
        other = close_sequences(origin,(b'AB',b'x',b'y'),(0,1,0,2),(1,2,3),(Fraction(0),)*8)
        self.assertEqual(other.restore(),table.restore())
        self.assertNotEqual(tuple(self.geometry.lift(o.source_state) for _,o in other.wire_occurrences()),
                            tuple(self.geometry.lift(o.source_state) for _,o in table.wire_occurrences()))

    def test_recover_from_circle_positions(self):
        table = self.fixture()
        rebuilt = self.replay(table)
        self.assertEqual(rebuilt.receipt(),table.receipt())
        self.assertEqual(rebuilt.restore(),b'ABxABy')
        # Circle 1's space relation moves its second occurrence ahead of its first.
        self.assertEqual(tuple(o.source_offset for _,o in table.wire_occurrences())[:2],(3,0))

    def test_all_seven_circles_participate(self):
        blocks = tuple(bytes([i,0,i]) for i in range(7))
        order = tuple(range(7))*3
        origin = ByteOrigin(b''.join(blocks[i] for i in order),'seven',0,self.geometry)
        table = close_sequences(origin,blocks,order,tuple(range(1,8)),SPACES)
        self.assertEqual({o.circle for _,o in table.wire_occurrences()},set(range(1,8)))
        self.assertEqual(self.replay(table).restore(),origin.source)

    def test_round_context_changes_frame_not_message(self):
        a = ByteOrigin(b'AB','one',0,self.geometry)
        b = ByteOrigin(b'BA','one',1,self.geometry,a.message_origin)
        self.assertEqual(a.message_origin,b.message_origin)
        self.assertNotEqual(a.identity,b.identity)
        self.assertNotEqual(a.byte_axis(0),b.byte_axis(0))
        with self.assertRaises(BinaryError):
            ByteOrigin(b'AB','one',0,self.geometry,'0'*64)
        with self.assertRaises(BinaryError):
            ByteOrigin(b'AB','one',1,self.geometry)

    def test_leading_zero_and_empty_sources(self):
        data=b'\x00\x00A\x00\x00A'
        origin=ByteOrigin(data,'zeros',0,self.geometry)
        table=close_sequences(origin,(b'\x00\x00A',),(0,0),(1,),SPACES)
        self.assertEqual(self.replay(table).restore(),data)
        empty=ByteOrigin(b'','empty',0,self.geometry)
        self.assertEqual(close_sequences(empty,(),(),(),SPACES).restore(),b'')
        with self.assertRaises(BinaryError):
            empty.byte_axis(0)

    def test_bad_partitions_refuse(self):
        o=ByteOrigin(b'ABAB','bad',0,self.geometry)
        bad=(( (b'AB',),(0,),(1,),SPACES),
             ( (b'AB',b'AB'),(0,1),(1,2),SPACES),
             ( (b'AB',),(0,0),(0,),SPACES),
             ( (b'AB',),(True,0),(1,),SPACES),
             ( (b'AB',),[0,0],(1,),SPACES),
             ( (b'AB',),(0,0),(1,),(0,)*8))
        for args in bad:
            with self.assertRaises(BinaryError):
                close_sequences(o,*args)

    def test_bad_coordinate_counts_gaps_and_frames_refuse(self):
        t=self.fixture()
        wire=t.wire_occurrences()
        positions=tuple(self.geometry.lift(o.source_state) for _,o in wire)
        for changes in (dict(counts=(0,)*7),dict(source_turns=(Fraction(1,11),)+positions[1:]),
                        dict(source_turns=(positions[1],)+positions[1:]),dict(max_bytes=5),
                        dict(source_turns=(positions[0]+1,)+positions[1:])):
            with self.assertRaises(ValueError):
                self.replay(t,**changes)

    def test_work_graph_identity(self):
        path = Path(__file__).resolve().parents[1]/'work-graph.json'
        record = json.loads(path.read_text())
        payload = {k:record[k] for k in ('repositories','boundaries')}
        digest = sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        self.assertEqual(digest,record['work_graph_sha256'])
        entries = {e['repository']:e for e in record['repositories']}
        self.assertEqual(entries['The-Interdependency/ucns']['commit'],UCNS_COMMIT)
        self.assertFalse(record['boundaries']['authority_transfer'])
        self.assertTrue(record['boundaries']['hmmm'])

    def test_changed_native_source_refuses_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'src/ucns';path.mkdir(parents=True)
            marker=root/'executed'
            (path/'axis_circle.py').write_text(f"open({str(marker)!r},'w').write('bad')")
            with self.assertRaises(BinaryError):
                Geometry(root)
            self.assertFalse(marker.exists())


if __name__=='__main__':
    unittest.main()
