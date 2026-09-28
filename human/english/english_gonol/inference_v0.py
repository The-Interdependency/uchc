# === MODULE_BUILD ===
# id: uchc_english_inference_v0
#   module_name: inference_v0
#   module_kind: candidate
#   summary: option-preserving inference engine v0 - every named channel map fires over every definition_id unreduced, producing composite, lifted, and placement receipts with named refusals
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, UCNS_INFERENCE_COMMIT, UCNS_DISPLACEMENT_LAW_MODULE_SHA256, UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256, UCNS_PLACEMENT_FRAME_MODULE_SHA256, Refusal, Bundle, channel_map_ids, zero_channel_control, infer, infer_definition, bundle_bytes
#   internal_surface: verified ucns consumption, channel maps, refusal clauses, receipt assembly
#   auth_boundary: none
#   storage_boundary: read only over the construct; receipts are immutable records
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: tests.test_inference_v0
#   rollout: inference beginning over UCHC; no winner is picked
#   rollback: remove this module and its tests
#   requires: uchc_english_inference_input, ucns_displacement_law, ucns_lifted_displacement, ucns_placement_frame
#   since: 2026-09-28
#   unresolved: sense selection, learned angles, canon ratification, and one-map-as-The-Law are NOT DONE
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: inference_v0_option_preserving
#   given: one admitted frame and a verified ucns checkout
#   then: every runnable map fires over every definition_id unreduced and no map is preferred
#   class: doctrine
# id: inference_v0_named_refusals
#   given: a map whose field is missing
#   then: the bundle carries a named refusal clause, never a silent skip
#   class: correctness
# id: inference_v0_receipts_record_both_angle_stories
#   given: one fired map
#   then: composite, lifted, and placement receipts all appear; the dead visible turn stays in the composite receipt and is not the readout
#   class: correctness
# id: inference_v0_covering_recorded_not_searched
#   given: one fired map
#   then: covering d is recorded unset and as the single bijective witness 158 without any search
#   class: doctrine
# id: inference_v0_zero_is_identity
#   given: the zero-channel control
#   then: (0,0,0) produces the identity turn and placement origin exactly
#   class: correctness
# === END CONTRACTS ===
"""Option-preserving inference engine v0.

text -> InferenceFrame -> each runnable map -> each definition_id unreduced
-> (o, s, c) -> composite + lifted + placement receipts.

Missing fields are named refusals. The dead visible ordered-concatenation
turn stays inside the composite receipt; the readout is lifted plus
placement. Covering d is recorded unset and as the one bijective witness
158, without searching d. No map is declared The Law.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from .inference_input import EnglishConstruct, InferenceFrame

SCHEMA = "uchc.english.inference-v0"
VERSION = "0.1.0"
_MODULUS = 157

UCNS_INFERENCE_COMMIT = "fc01e1f0323da45362704f92adbf6d3b8a008307"
UCNS_DISPLACEMENT_LAW_MODULE_SHA256 = "8d7207e5191da9e7de3f084fdba033b9478f16dbf3c6724a709c08a0d024ee02"
UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256 = "670c4e41f130b2d6b2439ee17c65bc699985d18e36d4958edbdb06e445c2c037"
UCNS_PLACEMENT_FRAME_MODULE_SHA256 = "27608365b9f42dbb59cd15c27525b697ca8cf33ad4f2b51db8a3b417b74c95e0"


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


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load_verified_ucns(root: Path) -> tuple[Any, Any, Any]:
    root = Path(root)
    modules = (
        ("displacement_law.py", UCNS_DISPLACEMENT_LAW_MODULE_SHA256),
        ("lifted_displacement.py", UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256),
        ("placement_frame.py", UCNS_PLACEMENT_FRAME_MODULE_SHA256),
    )
    for name, digest in modules:
        path = root / "src" / "ucns" / name
        if not path.exists():
            raise InferenceV0Error(f"ucns {name} missing under {root}")
        if _sha256(path) != digest:
            raise InferenceV0Error(f"ucns {name} bytes do not match the pinned commit")
    try:
        subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor",
             UCNS_INFERENCE_COMMIT, "HEAD"],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        raise InferenceV0Error("ucns checkout does not contain the pinned inference commit") from exc
    package = root / "src"
    sys.path.insert(0, str(package))
    try:
        from ucns.displacement_law import build_displacement  # type: ignore
        from ucns.lifted_displacement import build_lifted_displacement  # type: ignore
        from ucns.placement_frame import build_placement_frame  # type: ignore
    finally:
        sys.path.pop(0)
    return build_displacement, build_lifted_displacement, build_placement_frame


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


def _receipts(ucns: tuple[Any, Any, Any], o: int, s: int, c: int) -> dict[str, Any]:
    build_displacement, build_lifted_displacement, build_placement_frame = ucns
    composite = build_displacement(o, s, c)
    lifted_unset = build_lifted_displacement(o, s, c)
    lifted_d158 = build_lifted_displacement(o, s, c, covering_degree=158)
    placement = build_placement_frame(o, s, c)
    return {
        "composite": composite.as_dict() if hasattr(composite, "as_dict") else composite,
        "lifted_unset": lifted_unset.as_dict(),
        "lifted_bijective_158": lifted_d158.as_dict(),
        "placement": placement.as_dict(),
        "readout": "lifted + placement; the dead visible turn stays in the composite receipt",
    }


@dataclass(frozen=True)
class Bundle:
    map_id: str
    definition_id: int
    channels: tuple[int, int, int] | None
    receipts: dict[str, Any] | None
    refusals: tuple[Refusal, ...]
    covering: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "version": VERSION,
            "map_id": self.map_id,
            "definition_id": self.definition_id,
            "channels": list(self.channels) if self.channels is not None else None,
            "receipts": self.receipts,
            "refusals": [refusal.as_dict() for refusal in self.refusals],
            "covering": self.covering,
        }

    def bytes(self) -> bytes:
        return _canonical(self.as_dict())


def _resolve_channel(name: str, record: Any, frame: InferenceFrame,
                     corpus: EnglishConstruct) -> int | Refusal:
    return CHANNEL_MAPS[name](record, frame, corpus)


def _build_bundle(map_id: str, record: Any, frame: InferenceFrame,
                  corpus: EnglishConstruct, ucns: tuple[Any, Any, Any]) -> Bundle:
    o_name, s_name, c_name = map_id.split("|")
    o_value = _resolve_channel(o_name, record, frame, corpus)
    s_value = _resolve_channel(s_name, record, frame, corpus)
    c_value = _resolve_channel(c_name, record, frame, corpus)
    refusals = tuple(
        Refusal(name, value.clause)
        for name, value in ((o_name, o_value), (s_name, s_value), (c_name, c_value))
        if isinstance(value, Refusal)
    )
    covering = {"unset": True, "bijective_d": 158, "searched": False}
    if refusals:
        return Bundle(map_id, record.gonol.definition_id, None, None, refusals, covering)
    o, s, c = o_value, s_value, c_value
    return Bundle(map_id, record.gonol.definition_id, (o, s, c),
                  _receipts(ucns, o, s, c), refusals, covering)


def infer(frame: InferenceFrame, corpus: EnglishConstruct, ucns_source_root: Path) -> list[Bundle]:
    """Run every map combination over every definition_id unreduced."""

    ucns = _load_verified_ucns(Path(ucns_source_root))
    bundles: list[Bundle] = []
    for word in frame.words:
        for definition_id in word.definition_ids:
            record = corpus.definition(definition_id)
            for o_name in O_MAPS:
                for s_name in S_MAPS:
                    for c_name in C_MAPS:
                        map_id = f"{o_name}|{s_name}|{c_name}"
                        bundles.append(_build_bundle(map_id, record, frame, corpus, ucns))
    return bundles


def infer_definition(frame: InferenceFrame, corpus: EnglishConstruct,
                     definition_id: int, ucns_source_root: Path) -> list[Bundle]:
    """Run every map combination over one explicit definition_id."""

    ucns = _load_verified_ucns(Path(ucns_source_root))
    record = corpus.definition(definition_id)
    return [
        _build_bundle(f"{o_name}|{s_name}|{c_name}", record, frame, corpus, ucns)
        for o_name in O_MAPS
        for s_name in S_MAPS
        for c_name in C_MAPS
    ]


def zero_channel_control(ucns_source_root: Path) -> dict[str, Any]:
    """(0,0,0) must produce the identity turn and the placement origin."""

    build_displacement, build_lifted_displacement, build_placement_frame = _load_verified_ucns(
        Path(ucns_source_root))
    lifted = build_lifted_displacement(0, 0, 0)
    placement = build_placement_frame(0, 0, 0)
    composite = build_displacement(0, 0, 0)
    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "control": "zero-channel identity",
        "lifted": lifted.as_dict(),
        "placement": placement.as_dict(),
        "composite": composite.as_dict(),
        "identity_ok": (
            lifted.phase_turns.numerator == 0
            and lifted.frame == "positive-local-frame"
            and placement.angle_turn.numerator == 0
            and placement.radius == 0.0
            and placement.layer == 0
        ),
    }
    payload["receipt_sha256"] = sha256(_canonical(payload)).hexdigest()
    return payload


def bundle_bytes(bundle: Bundle) -> bytes:
    return bundle.bytes()


__all__ = [
    "SCHEMA",
    "VERSION",
    "UCNS_INFERENCE_COMMIT",
    "UCNS_DISPLACEMENT_LAW_MODULE_SHA256",
    "UCNS_LIFTED_DISPLACEMENT_MODULE_SHA256",
    "UCNS_PLACEMENT_FRAME_MODULE_SHA256",
    "InferenceV0Error",
    "Refusal",
    "Bundle",
    "CHANNEL_MAPS",
    "channel_map_ids",
    "zero_channel_control",
    "infer",
    "infer_definition",
    "bundle_bytes",
]
