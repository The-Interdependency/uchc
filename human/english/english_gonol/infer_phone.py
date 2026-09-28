# === MODULE_BUILD ===
# id: uchc_english_infer_phone
#   module_name: infer_phone
#   module_kind: tool
#   summary: one tool, infer-phone - text plus optional K in, ResponseCard out, through uchc.respond_v0.respond
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, InferPhoneError, run_phone, build_response_card
#   internal_surface: argparse CLI, verified EnglishConstruct open, respond_v0 call, canonical stdout print
#   auth_boundary: none
#   storage_boundary: read only over the construct; no writes
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: tests.test_infer_phone
#   rollout: the single inference phone tool; no law is picked
#   rollback: remove this module and its tests
#   requires: uchc_english_inference_input, uchc_english_respond_v0
#   since: 2026-09-28
#   unresolved: sense selection and one-map-as-The-Law remain NOT DONE
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: infer_phone_calls_respond
#   given: text and an optional K
#   then: the tool prints exactly the respond_v0 response card and nothing else on stdout
#   class: correctness
# id: infer_phone_empty_is_empty_card
#   given: empty text
#   then: the tool prints the empty card with exit code 0, not an answer and not an error
#   class: correctness
# id: infer_phone_fails_closed
#   given: missing artifacts, wrong identities, or invalid input
#   then: the tool exits nonzero with a diagnostic on stderr and prints nothing on stdout
#   class: safety
# === END CONTRACTS ===
"""infer-phone: one tool.

    python -m english_gonol.infer_phone TEXT \
        --construct-db PATH --database-sha256 HEX --logical-receipt HEX \
        --ucns-source-root PATH [--K one-def]

Prints the ResponseCard produced by respond_v0.respond.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .inference_input import EnglishConstruct
from .respond_v0 import respond

SCHEMA = "uchc.english.infer-phone"
VERSION = "0.1.0"


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
    ucns_source_root: Path,
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
    parser.add_argument("--ucns-source-root", required=True,
                        help="path to the pinned ucns checkout")
    parser.add_argument("--K", default="one-def", help="respond mode; only one-def is implemented")
    args = parser.parse_args(list(argv))

    try:
        card = build_response_card(
            args.text,
            Path(args.construct_db),
            args.database_sha256,
            args.logical_receipt,
            Path(args.ucns_source_root),
            K=args.K,
        )
    except Exception as exc:  # fail closed on any admission/receipt error
        print(f"infer-phone: {exc}", file=sys.stderr)
        return 1

    sys.stdout.write(_canonical(card).decode("utf-8") + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_phone(sys.argv[1:]))
