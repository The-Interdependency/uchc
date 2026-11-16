"""Resolve every named channel combination against each stored definition in source order."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable

from .inference_input import EnglishConstruct, InferenceFrame

SCHEMA = "uchc.english.inference-v0"
VERSION = "0.2.0"

class InferenceV0Error(ValueError):
    """Raised when the inference engine fails closed."""


@dataclass(frozen=True)
class Refusal:
    map_id: str
    clause: str

    def as_dict(self) -> dict[str, str]:
        return {"map_id": self.map_id, "clause": self.clause}


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _first_occurrence(frame: InferenceFrame, word_id: int) -> int | None:
    for occurrence in frame.occurrences:
        if occurrence.kind == "word" and occurrence.identity_id == word_id:
            return occurrence.ordinal
    return None


def _origin_word_id(record: Any) -> int:
    return record.gonol.origin_word_id


def _o1(record: Any, frame: InferenceFrame, corpus: EnglishConstruct) -> int | Refusal:
    return record.gonol.ordinal


def _o2(record: Any, frame: InferenceFrame, corpus: EnglishConstruct) -> int | Refusal:
    ordinal = _first_occurrence(frame, _origin_word_id(record))
    if ordinal is None:
        return Refusal("O2.frame_occurrence_index", "identity/occurrence collapse")
    return ordinal


def _o3(record: Any, frame: InferenceFrame, corpus: EnglishConstruct) -> int | Refusal:
    if not record.components:
        return Refusal("O3.gonol_position_sum", "no integer in stored E")
    return sum(component.identity_id for component in record.components)


def _o4(record: Any, frame: InferenceFrame, corpus: EnglishConstruct) -> int | Refusal:
    if not record.components:
        return Refusal("O4.first_scalar_gonol", "no integer in stored E")
    return record.components[0].identity_id


def _s1(record: Any, frame: InferenceFrame, corpus: EnglishConstruct) -> int | Refusal:
    origin = corpus.word_by_id(_origin_word_id(record))
    if record.gonol.definition_id not in origin.definition_ids:
        return Refusal("S1.source_order_index", "not determined")
    return origin.definition_ids.index(record.gonol.definition_id) + 1


def _s2(record: Any, frame: InferenceFrame, corpus: EnglishConstruct) -> int | Refusal:
    return len(record.components)


def _s3(record: Any, frame: InferenceFrame, corpus: EnglishConstruct) -> int | Refusal:
    return record.definition_index


def _s4(record: Any, frame: InferenceFrame, corpus: EnglishConstruct) -> int | Refusal:
    value = len(record.components)
    if value == 0:
        return Refusal("S4.refuse_s_zero", "semantic hole")
    return value


def _c1(record: Any, frame: InferenceFrame, corpus: EnglishConstruct) -> int | Refusal:
    ordinal = _first_occurrence(frame, _origin_word_id(record))
    if ordinal is None:
        return Refusal("C1.sentence_position", "identity/occurrence collapse")
    return ordinal


def _c2(record: Any, frame: InferenceFrame, corpus: EnglishConstruct) -> int | Refusal:
    identities = [component.identity_id for component in record.components]
    if len(identities) < 2:
        return Refusal("C2.neighbor_gonol_sum", "not determined")
    return 2 * sum(identities) - identities[0] - identities[-1]


def _c3(record: Any, frame: InferenceFrame, corpus: EnglishConstruct) -> int | Refusal:
    return 0 if record.previous_definition_id is None else record.definition_index


CHANNEL_MAPS: dict[str, Callable[[Any, InferenceFrame, EnglishConstruct], int | Refusal]] = {
    "O1.definition_ordinal": _o1,
    "O2.frame_occurrence_index": _o2,
    "O3.gonol_position_sum": _o3,
    "O4.first_scalar_gonol": _o4,
    "S1.source_order_index": _s1,
    "S2.component_count": _s2,
    "S3.chain_depth": _s3,
    "S4.refuse_s_zero": _s4,
    "C1.sentence_position": _c1,
    "C2.neighbor_gonol_sum": _c2,
    "C3.topology_layer_only": _c3,
}

O_MAPS = [name for name in CHANNEL_MAPS if name.startswith("O")]
S_MAPS = [name for name in CHANNEL_MAPS if name.startswith("S")]
C_MAPS = [name for name in CHANNEL_MAPS if name.startswith("C")]


def channel_map_ids() -> tuple[str, ...]:
    return tuple(CHANNEL_MAPS)


@dataclass(frozen=True)
class Bundle:
    map_id: str
    definition_id: int
    channels: tuple[int, int, int] | None
    refusals: tuple[Refusal, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "version": VERSION,
            "map_id": self.map_id,
            "definition_id": self.definition_id,
            "channels": list(self.channels) if self.channels is not None else None,
            "refusals": [refusal.as_dict() for refusal in self.refusals],
        }

    def bytes(self) -> bytes:
        return _canonical(self.as_dict())


def _resolve_channel(name: str, record: Any, frame: InferenceFrame,
                     corpus: EnglishConstruct) -> int | Refusal:
    return CHANNEL_MAPS[name](record, frame, corpus)


def _build_bundle(map_id: str, record: Any, frame: InferenceFrame,
                  corpus: EnglishConstruct) -> Bundle:
    o_name, s_name, c_name = map_id.split("|")
    o_value = _resolve_channel(o_name, record, frame, corpus)
    s_value = _resolve_channel(s_name, record, frame, corpus)
    c_value = _resolve_channel(c_name, record, frame, corpus)
    refusals = tuple(
        Refusal(name, value.clause)
        for name, value in ((o_name, o_value), (s_name, s_value), (c_name, c_value))
        if isinstance(value, Refusal)
    )
    channels = None if refusals else (o_value, s_value, c_value)
    return Bundle(map_id, record.gonol.definition_id, channels, refusals)


def infer(frame: InferenceFrame, corpus: EnglishConstruct, ucns_source_root: Path | None = None) -> list[Bundle]:
    """Run every map combination over every definition_id unreduced."""

    bundles: list[Bundle] = []
    for word in frame.words:
        for definition_id in word.definition_ids:
            record = corpus.definition(definition_id)
            for o_name in O_MAPS:
                for s_name in S_MAPS:
                    for c_name in C_MAPS:
                        map_id = f"{o_name}|{s_name}|{c_name}"
                        bundles.append(_build_bundle(map_id, record, frame, corpus))
    return bundles


def infer_definition(frame: InferenceFrame, corpus: EnglishConstruct,
                     definition_id: int, ucns_source_root: Path | None = None) -> list[Bundle]:
    """Run every map combination over one explicit definition_id."""

    record = corpus.definition(definition_id)
    return [
        _build_bundle(f"{o_name}|{s_name}|{c_name}", record, frame, corpus)
        for o_name in O_MAPS
        for s_name in S_MAPS
        for c_name in C_MAPS
    ]


def bundle_bytes(bundle: Bundle) -> bytes:
    return bundle.bytes()


__all__ = [
    "SCHEMA",
    "VERSION",
    "InferenceV0Error",
    "Refusal",
    "Bundle",
    "CHANNEL_MAPS",
    "channel_map_ids",
    "infer",
    "infer_definition",
    "bundle_bytes",
]
