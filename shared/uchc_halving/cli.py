# ratios: loc_comments=22:1 imports_exports=4:1 calls_definitions=12:1
"""Run uchc-halving bull, or uchc-halving --sequence bull bull."""
import argparse
import json
from fractions import Fraction

from . import closed_record, construct_sequence, construct_text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('text', nargs='+')
    parser.add_argument('--sequence', action='store_true', help='stack each supplied text as a closed child')
    parser.add_argument('--radius', type=Fraction, default=1, help='exact parent-frame radius')
    parser.add_argument('--ucns-source-root', help='use the pinned UCNS source instead of its installation')
    args = parser.parse_args(argv)
    opts = {'ucns_source_root': args.ucns_source_root}
    if args.sequence:
        words = tuple(construct_text(text, **opts) for text in args.text)
        obj = construct_sequence(words, placement_radius=args.radius, **opts)
    else:
        if len(args.text) != 1:
            parser.error('pass one quoted text or use --sequence')
        obj = construct_text(args.text[0], placement_radius=args.radius, **opts)
    print(json.dumps({'closed': closed_record(obj, **opts),
                      'radii': [[r.radius.numerator, r.radius.denominator] for r in obj.rays],
                      'recovered': ''.join(obj.recover())}, sort_keys=True))
# ratios: loc_comments=22:1 imports_exports=4:1 calls_definitions=12:1
