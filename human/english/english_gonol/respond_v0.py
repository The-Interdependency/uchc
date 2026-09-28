# === MODULE_BUILD ===
# id: uchc_english_respond_v0
#   module_name: respond_v0
#   module_kind: surface
#   summary: response surface over inference_v0 - one motion card per turn, no winner, empty input is an empty card not an answer
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, RespondError, respond
#   internal_surface: infer() reuse, first-fired bundle sampling, refusal surfacing, hidden bundle count
#   auth_boundary: none
#   storage_boundary: read only over the construct; responses are immutable records
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: tests.test_respond_v0
#   rollout: inference response surface; no law is picked
#   rollback: remove this module and its tests
#   requires: uchc_english_inference_input, uchc_english_inference_v0
#   since: 2026-09-28
#   unresolved: sense selection and one-map-as-The-Law remain NOT DONE; K accepts only "one-def"
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: respond_v0_uses_infer
#   given: an admitted text
#   then: the response is produced from inference_v0.infer bundles and never recomputes geometry
#   class: correctness
# id: respond_v0_one_motion_card_no_winner
#   given: fired bundles exist
#   then: exactly one motion card is returned as a sample, labeled not-selected
#   class: doctrine
# id: respond_v0_empty_is_not_an_answer
#   given: empty text
#   then: the response is an empty card with zero hidden bundles, never an answer
#   class: correctness
# id: respond_v0_named_refusals
#   given: an unsupported K or bundles with refusals
#   then: the response surfaces named refusal clauses, never a silent skip
#   class: correctness
# === END CONTRACTS ===
"""Response surface over inference_v0.

respond(text, K="one-def") returns one motion card sampled from the fired
bundles (never a winner), the first eight definition ids, surfaced
refusals, and the hidden bundle count. Empty text yields an empty card,
not an answer. No law is picked.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .inference_input import EnglishConstruct
from .inference_v0 import Bundle, infer

SCHEMA = "uchc.english.respond-v0"
VERSION = "0.1.0"


class RespondError(ValueError):
    """Raised when the response surface fails closed."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _motion_card(bundle: Bundle) -> dict[str, Any]:
    receipts = bundle.receipts
    lifted = receipts["lifted_unset"]
    placement = receipts["placement"]
    return {
        "map_id": bundle.map_id,
        "definition_id": bundle.definition_id,
        "channels": list(bundle.channels) if bundle.channels is not None else None,
        "lifted": {
            "phase_turns": lifted["mobius"]["phase_turns"],
            "frame": lifted["mobius"]["frame"],
            "covering_degree": lifted["covering_degree"],
            "receipt_sha256": lifted["receipt_sha256"],
        },
        "placement": {
            "angle_turn": placement["angle_turn"],
            "radius": placement["radius"],
            "layer": placement["layer"],
            "receipt_sha256": placement["receipt_sha256"],
        },
        "sample_not_selected": True,
    }


def respond(
    text: str,
    corpus: EnglishConstruct,
    ucns_source_root: Path,
    *,
    K: str = "one-def",
) -> dict[str, Any]:
    """Return one motion card for text; empty text is an empty card."""

    if type(text) is not str:
        raise TypeError("text must be str, without coercion")
    if K != "one-def":
        payload = {
            "schema": SCHEMA,
            "version": VERSION,
            "text": text,
            "words": [],
            "def_ids": [],
            "motion_card": None,
            "refuse": [{"map_id": "K", "clause": "not determined: only K='one-def' is implemented"}],
            "bundle_count_hidden": 0,
            "hmmm": "no winner",
        }
        payload["receipt_sha256"] = sha256(_canonical(payload)).hexdigest()
        return payload

    frame = corpus.resolve_text(text, source_id="respond:" + sha256(text.encode("utf-8")).hexdigest()[:16])
    if not text:
        payload = {
            "schema": SCHEMA,
            "version": VERSION,
            "text": "",
            "words": [],
            "def_ids": [],
            "motion_card": None,
            "refuse": [],
            "bundle_count_hidden": 0,
            "empty_is_not_an_answer": True,
            "hmmm": "no winner",
        }
        payload["receipt_sha256"] = sha256(_canonical(payload)).hexdigest()
        return payload

    frame = frame.require_complete()
    bundles = infer(frame, corpus, ucns_source_root)
    fired = [bundle for bundle in bundles if bundle.receipts is not None]

    words = [word.gonol.surface for word in frame.words]
    def_ids: list[int] = []
    for word in frame.words:
        for definition_id in word.definition_ids:
            if definition_id not in def_ids:
                def_ids.append(definition_id)
            if len(def_ids) >= 8:
                break
        if len(def_ids) >= 8:
            break

    refusals = [
        refusal.as_dict()
        for bundle in bundles
        for refusal in bundle.refusals
    ]

    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "text": text,
        "words": words,
        "def_ids": def_ids,
        "motion_card": _motion_card(fired[0]) if fired else None,
        "refuse": refusals,
        "bundle_count_hidden": len(bundles),
        "hmmm": "no winner",
    }
    payload["receipt_sha256"] = sha256(_canonical(payload)).hexdigest()
    return payload


__all__ = ["SCHEMA", "VERSION", "RespondError", "respond"]
