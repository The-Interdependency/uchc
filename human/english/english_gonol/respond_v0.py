# === MODULE_BUILD ===
# id: uchc_english_respond_v0
#   module_name: respond_v0
#   module_kind: surface
#   summary: Sample the first available dictionary evidence bundle and retain candidate order.
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, RespondError, respond
#   internal_surface: dictionary lookup, evidence sampling and response digest
#   auth_boundary: none
#   storage_boundary: read only over the construct; responses are immutable records
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: tests.test_respond_v0
#   rollout: verified English dictionary consumer
#   rollback: remove this module and its tests
#   requires: uchc_english_inference_input, uchc_english_inference_v0
#   since: 2026-09-28
#   unresolved: contextual sense selection
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: respond_v0_uses_infer
#   given: an admitted text
#   then: sample the bundles returned by infer
#   class: correctness
# id: respond_v0_evidence_card
#   given: at least one runnable bundle
#   then: identify its source construct and sample the first runnable bundle
#   class: correctness
# id: respond_v0_empty_is_not_an_answer
#   given: empty input
#   then: return an empty evidence card and zero candidates
#   class: correctness
# id: respond_v0_named_refusals
#   given: an unsupported mode
#   then: surface its refusal
#   class: correctness
# === END CONTRACTS ===
"""Sample the first available dictionary evidence bundle and retain candidate order."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .inference_input import EnglishConstruct
from .inference_v0 import Bundle, infer

SCHEMA = "uchc.english.respond-v0"
VERSION = "0.2.0"


class RespondError(ValueError):
    """Raised when the response surface fails closed."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _evidence_card(bundle: Bundle) -> dict[str, Any]:
    return {**bundle.as_dict(), "sample_not_selected": True}


def respond(
    text: str,
    corpus: EnglishConstruct,
    ucns_source_root: Path | None = None,
    *,
    K: str = "one-def",
) -> dict[str, Any]:
    """Return one evidence card for text; empty text is an empty card."""

    if type(text) is not str:
        raise TypeError("text must be str, without coercion")
    construct = {
        "database_sha256": corpus.identity.database_sha256,
        "logical_receipt": corpus.identity.logical_receipt,
    }
    if K != "one-def":
        payload = {
            "schema": SCHEMA,
            "version": VERSION,
            "construct": construct,
            "text": text,
            "words": [],
            "def_ids": [],
            "evidence_card": None,
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
            "construct": construct,
            "text": "",
            "words": [],
            "def_ids": [],
            "evidence_card": None,
            "refuse": [],
            "bundle_count_hidden": 0,
            "empty_is_not_an_answer": True,
            "hmmm": "no winner",
        }
        payload["receipt_sha256"] = sha256(_canonical(payload)).hexdigest()
        return payload

    frame = frame.require_complete()
    bundles = infer(frame, corpus, ucns_source_root)
    fired = [bundle for bundle in bundles if bundle.channels is not None]

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
        "construct": construct,
        "text": text,
        "words": words,
        "def_ids": def_ids,
        "evidence_card": _evidence_card(fired[0]) if fired else None,
        "refuse": refusals,
        "bundle_count_hidden": len(bundles),
        "hmmm": "no winner",
    }
    payload["receipt_sha256"] = sha256(_canonical(payload)).hexdigest()
    return payload


__all__ = ["SCHEMA", "VERSION", "RespondError", "respond"]
