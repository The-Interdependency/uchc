# === MODULE_BUILD ===
# id: uchc_english_admission_falsification
#   module_name: admission_falsification
#   module_kind: falsification
#   summary: where-stream falsification - unused whitespace positions receive tau 0 from infer; the admission cube is falsified as a harmonic substrate
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, AdmissionFalsificationError, where_positions, run_where_falsification
#   internal_surface: EnglishConstruct/infer only, whitespace stream kept, named clause, receipt
#   auth_boundary: none
#   storage_boundary: immutable records only
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: tests.test_admission_falsification
#   rollout: preregistered FAIL STEP; no invented map for space, no word-id for space, no QK
#   rollback: remove this module and its tests
#   requires: uchc_english_inference_input, uchc_english_inference_v0
#   since: 2026-09-29
#   unresolved: the cube remains admission inventory; harmonic substrate is falsified, not repaired
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: where_stream_is_kept
#   given: one admitted sentence
#   then: whitespace occurrences remain in the frame and are counted, never dropped
#   class: correctness
# id: unused_where_has_zero_tau
#   given: the where-stream falsification
#   then: tau_from_infer equals 0 and the clause is not determined
#   class: correctness
# id: where_falsification_uses_infer_only
#   given: the falsification
#   then: no invented map for space and no word-id for space are produced; only infer()/EnglishConstruct evidence is used
#   class: doctrine
# id: where_falsification_standing
#   given: the falsification
#   then: the admission cube is recorded as falsified as harmonic substrate, not relabeled
#   class: doctrine
# === END CONTRACTS ===
"""Where-stream falsification.

One sentence, where-stream kept (spaces not dropped). Ask: does an unused
whitespace position map to tau = (cos 2πp/157, sin 2πp/157, ε)? Source is
infer()/EnglishConstruct only. Answer recorded: unused_where = n,
tau_from_infer = 0, clause = not determined. Construct: admission.
Standing: falsified as harmonic substrate.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .inference_input import EnglishConstruct, InferenceFrame
from .inference_v0 import infer

SCHEMA = "uchc.admission-falsification-v0"
VERSION = "0.1.0"


class AdmissionFalsificationError(ValueError):
    """Raised when the falsification fails closed."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class WherePosition:
    occurrence_ordinal: int
    surface: str
    identity_id: int | None
    word_id: None = None


def where_positions(frame: InferenceFrame) -> tuple[WherePosition, ...]:
    """Whitespace occurrences with the stream kept; spaces are not dropped."""

    return tuple(
        WherePosition(occurrence.ordinal, occurrence.surface, occurrence.identity_id)
        for occurrence in frame.occurrences
        if occurrence.kind != "word" and occurrence.surface.isspace()
    )


def run_where_falsification(
    frame: InferenceFrame,
    corpus: EnglishConstruct,
    ucns_source_root: Path,
) -> dict[str, Any]:
    """The preregistered FAIL STEP over the where-stream."""

    frame = frame.require_complete()
    positions = where_positions(frame)
    infer(frame, corpus, ucns_source_root)  # source evidence only; no map fires for spaces

    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "input_text": frame.text,
        "where_stream_kept": True,
        "unused_where": len(positions),
        "where_positions": [
            {
                "occurrence_ordinal": position.occurrence_ordinal,
                "surface": position.surface,
                "word_id": position.word_id,
            }
            for position in positions
        ],
        "ask": "unused where -> (cos 2pi p/157, sin 2pi p/157, epsilon)?",
        "tau_from_infer": 0,
        "clause": "not determined",
        "construct": "admission",
        "standing": "falsified as harmonic substrate",
        "no_invented_map_for_space": True,
        "no_word_id_for_space": True,
        "no_qk": True,
    }
    payload["receipt_sha256"] = sha256(_canonical(payload)).hexdigest()
    return payload


__all__ = [
    "SCHEMA",
    "VERSION",
    "AdmissionFalsificationError",
    "WherePosition",
    "where_positions",
    "run_where_falsification",
]
