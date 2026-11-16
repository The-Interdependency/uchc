"""Read candidate dictionary evidence from a verified construct."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .inference_input import EnglishConstruct
from .respond_v0 import respond

SCHEMA = "uchc.english.infer-phone"
VERSION = "0.2.0"


class InferPhoneError(ValueError):
    """Raised when the phone fails closed."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def build_response_card(
    text: str,
    construct_db: Path,
    database_sha256: str,
    logical_receipt: str,
    ucns_source_root: Path | None = None,
    *,
    K: str = "one-def",
) -> dict[str, Any]:
    """Open the verified construct once and return the respond card."""

    with EnglishConstruct(construct_db, database_sha256=database_sha256,
                          logical_receipt=logical_receipt) as corpus:
        return respond(text, corpus, ucns_source_root, K=K)


def run_phone(argv: Sequence[str]) -> int:
    """CLI entry. Returns the process exit code."""

    parser = argparse.ArgumentParser(
        prog="infer-phone",
        description="one tool: text plus optional K in, ResponseCard out",
    )
    parser.add_argument("text", help="input text (quoted; may be empty string)")
    parser.add_argument("--construct-db", required=True, help="path to construct.db")
    parser.add_argument("--database-sha256", required=True,
                        help="trusted sha256 of construct.db")
    parser.add_argument("--logical-receipt", required=True,
                        help="trusted complete logical receipt")
    parser.add_argument("--ucns-source-root", help=argparse.SUPPRESS)
    parser.add_argument("--K", default="one-def", help="respond mode; only one-def is implemented")
    args = parser.parse_args(list(argv))

    try:
        card = build_response_card(
            args.text,
            Path(args.construct_db),
            args.database_sha256,
            args.logical_receipt,
            K=args.K,
        )
    except Exception as exc:  # fail closed on any admission/receipt error
        print(f"infer-phone: {exc}", file=sys.stderr)
        return 1

    sys.stdout.write(_canonical(card).decode("utf-8") + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_phone(sys.argv[1:]))
