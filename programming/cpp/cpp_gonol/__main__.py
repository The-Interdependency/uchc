# ratios: loc_comments=48:2 imports_exports=7:1 calls_definitions=29:2
"""Run python -m cpp_gonol build, verify or recover. Use --help for the arguments."""
import argparse
import json
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile

from . import construct, replay


def _publish(path, data):
    # A hard link publishes a complete file and atomically refuses existing targets.
    staged = NamedTemporaryFile(dir=path.parent, delete=False)
    temporary = Path(staged.name)
    try:
        with staged:
            staged.write(data)
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    cmds = parser.add_subparsers(dest="action", required=True)
    build = cmds.add_parser("build", help="construct one UTF-8 C++23 source file")
    build.add_argument("input", type=Path)
    build.add_argument("output", type=Path)
    build.add_argument("--source-id")
    build.add_argument("--bindings", action="store_true", help="require the int-main binding profile")
    verify = cmds.add_parser("verify", help="replay a construct, optionally against original bytes")
    verify.add_argument("input", type=Path)
    verify.add_argument("--original", type=Path)
    recover = cmds.add_parser("recover", help="write exact verified source bytes to a new path")
    recover.add_argument("input", type=Path)
    recover.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "build":
            record = construct(args.input.read_bytes(), source_id=args.input.name if args.source_id is None else args.source_id,
                               bindings=args.bindings)
            payload = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            _publish(args.output, (payload + "\n").encode("ascii"))
        else:
            record = json.loads(args.input.read_bytes())
            reference = args.original.read_bytes() if args.action == "verify" and args.original else None
            data = replay(record, original=reference)
            if args.action == "recover":
                _publish(args.output, data)
        print(record["receipt"])
    except (ValueError, OSError, ImportError) as exc:
        parser.exit(1, f"cpp_gonol: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())
# ratios: loc_comments=48:2 imports_exports=7:1 calls_definitions=29:2
