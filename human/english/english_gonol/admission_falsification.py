"""Record whitespace occurrences preserved by admission."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .inference_input import EnglishConstruct, InferenceFrame

SCHEMA = "uchc.admission-falsification-v0"
VERSION = "0.2.0"


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
    ucns_source_root: Path | None = None,
) -> dict[str, Any]:
    """Return the whitespace evidence from the admitted sentence."""

    frame = frame.require_complete()
    positions = where_positions(frame)

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
        "clause": "not determined",
        "construct": "admission",
        "no_invented_map_for_space": True,
        "no_word_id_for_space": True,
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
