"""Command line entry point for Python Gonol Construction.

Usage guidance::

    python -m python_gonol source.py --out-dir construct --ucns-source-root ~/src/ucns
    python -m python_gonol --verify construct --ucns-source-root ~/src/ucns

The construct is one compact SQLite database plus a small manifest.
"""

# === MODULE_BUILD ===
# id: python_gonol_cli
#   module_name: python_gonol.__main__
#   module_kind: adapter
#   summary: provides file-to-construct and construct verification commands
#   owner: Python Gonol Construction (stack-local research)
#   public_surface: python -m python_gonol
#   internal_surface: main
#   auth_boundary: none
#   storage_boundary: reads source or construct files and writes an explicitly named construct directory
#   network_boundary: none
#   user_data_boundary: read and write at caller-selected paths
#   admin_only: false
#   tests: tests.test_construct
#   rollout: explicit command only
#   rollback: remove the CLI while retaining the importable constructor
#   requires: python_gonol_construct
#   since: 2026-09-15
#   unresolved: streaming constructs for very large sources remain hmmm
# === END MODULE_BUILD ===

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .construct import (
    PythonGonolConstructionError,
    affixiate_python_bytes,
    verify_construct,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Construct Python 3.12 source with the English method."
    )
    parser.add_argument("source", nargs="?", help="Python source file")
    parser.add_argument("--out-dir", help="construct directory; required unless --verify")
    parser.add_argument("--ucns-source-root", required=True, help="UCNS checkout path")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verify", metavar="CONSTRUCT_DIR", help="verify an existing construct")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.verify:
        if args.source or args.out_dir:
            raise SystemExit("--verify does not accept source or --out-dir")
        try:
            receipt = verify_construct(Path(args.verify), args.ucns_source_root)
        except PythonGonolConstructionError as exc:
            print(f"verify failed: {exc}", file=sys.stderr)
            return 1
        print(f"verified {receipt}")
        return 0
    if not args.source or not args.out_dir:
        raise SystemExit("source and --out-dir are required unless --verify is used")
    try:
        result = affixiate_python_bytes(
            Path(args.source).read_bytes(),
            source_id=Path(args.source).as_posix(),
            ucns_source_root=args.ucns_source_root,
            state_dir=Path(args.out_dir),
            overwrite=args.overwrite,
        )
    except PythonGonolConstructionError as exc:
        print(f"construction failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"constructed {result.source_id} receipt={result.receipt_sha256} "
        f"occurrences={result.occurrence_count} characters={result.character_count} "
        f"controls={result.control_count} newlines={result.newline_count} "
        f"not_on_carrier={list(result.not_on_pinned_carrier)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
