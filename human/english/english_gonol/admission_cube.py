# === MODULE_BUILD ===
# id: uchc_english_admission_cube
#   module_name: admission_cube
#   module_kind: candidate
#   summary: Index glyph, word and definition occurrences for each dictionary channel combination.
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, MODES, AdmissionCubeError, HOLE, AdmissionCube, build_admission_cube, write_full_index_record, read_full_index_record, AdmissionWeights, admission_cube_phone_card
#   internal_surface: glyph, word and definition indices, named holes and replay
#   auth_boundary: none
#   storage_boundary: immutable records only; the full-index record is the stored object
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: tests.test_admission_cube
#   rollout: verified English dictionary consumer
#   rollback: remove this module and its tests
#   requires: uchc_english_inference_input, uchc_english_inference_v0
#   since: 2026-09-28
#   unresolved: contextual sense selection
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: admission_cube_has_all_modes
#   given: a complete text frame
#   then: index glyph, word and definition occurrences in every entry
#   class: correctness
# id: admission_cube_holes_are_named
#   given: an absent occurrence
#   then: retain its axis and reason
#   class: correctness
# id: admission_cube_verified_replay
#   given: a legacy schema, unexpected field or changed entry
#   then: refuse replay
#   class: correctness
# id: admission_cube_flattening_forbidden
#   given: a serialized full index
#   then: restore the same indices and allow contraction after replay
#   class: correctness
# id: admission_cube_weights_share_modes
#   given: weights on named axes
#   then: accept only the supported modes
#   class: correctness
# === END CONTRACTS ===
"""Index glyph, word and definition occurrences for each dictionary channel combination."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .inference_input import EnglishConstruct, InferenceFrame
from .inference_v0 import Bundle, infer

SCHEMA = "uchc.admission-cube-v0"
VERSION = "0.2.0"
MODES = ("g", "w", "d")
HOLE = "hole"

_HMMM = "if you can delete an index and the code still runs, you did not build the cube"


class AdmissionCubeError(ValueError):
    """Raised when the cube fails closed."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _first_word_occurrence(frame: InferenceFrame, word_id: int) -> int | None:
    for occurrence in frame.occurrences:
        if occurrence.kind == "word" and occurrence.identity_id == word_id:
            return occurrence.ordinal
    return None


def _first_glyph_occurrence(frame: InferenceFrame, word_id: int) -> int | None:
    for word in frame.words:
        if word.gonol.word_id == word_id:
            for occurrence in frame.occurrences:
                if occurrence.kind == "word" and occurrence.identity_id == word_id:
                    return occurrence.start
    return None


@dataclass(frozen=True)
class AdmissionCube:
    """One sentence fiber: admission indices per construct axis."""
    axes: dict[str, list[Any]]
    axis_holes: dict[str, list[str]]
    entries: tuple[dict[str, Any], ...]
    hmmm: str = _HMMM

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "version": VERSION,
            "axes": self.axes,
            "axis_holes": self.axis_holes,
            "entries": list(self.entries),
            "hmmm": self.hmmm,
        }

    def bytes(self) -> bytes:
        return _canonical(self.as_dict())

    def contract(self) -> dict[str, Any]:
        """Phone-card contraction: allowed only after the cube exists."""

        return {
            "schema": SCHEMA,
            "version": VERSION,
            "axes": {name: len(values) for name, values in self.axes.items()},
            "axis_holes": self.axis_holes,
            "entry_count": len(self.entries),
            "contracted": True,
            "hmmm": self.hmmm,
        }


def _hole(axis: str, reason: str) -> dict[str, str]:
    return {HOLE: reason, "axis": axis}


def build_admission_cube(
    frame: InferenceFrame,
    corpus: EnglishConstruct,
    ucns_source_root: Path | None = None,
    *,
    extra_definition_ids: tuple[int, ...] = (),
) -> AdmissionCube:
    """Build T from the full admitted frame and the full O x S x C receipts."""

    frame = frame.require_complete()
    bundles = infer(frame, corpus, ucns_source_root)

    axes: dict[str, list[Any]] = {mode: [] for mode in MODES}
    axis_holes: dict[str, list[str]] = {mode: [] for mode in MODES}
    seen: dict[str, set[Any]] = {mode: set() for mode in MODES}
    holes: dict[str, set[str]] = {mode: set() for mode in MODES}

    def index(axis: str, value: Any, reason: str | None = None) -> Any:
        if reason is not None:
            holes[axis].add(reason)
            return _hole(axis, reason)
        key = _canonical(value)
        if key not in seen[axis]:
            seen[axis].add(key)
            axes[axis].append(value)
        return value

    entries: list[dict[str, Any]] = []

    def add_entry(bundle: Bundle, g: Any, w: Any, d: Any) -> None:
        entry = {
            "g": g,
            "w": w,
            "d": d,
            "map_id": bundle.map_id,
            "fired": bundle.channels is not None,
        }
        entry["receipt_sha256"] = sha256(_canonical(entry)).hexdigest()
        entries.append(entry)

    for bundle in bundles:
        definition_id = bundle.definition_id
        record = corpus.definition(definition_id)
        origin_word_id = record.gonol.origin_word_id

        d_index = index("d", definition_id)

        word_occurrence = _first_word_occurrence(frame, origin_word_id)
        if word_occurrence is None:
            w_index = index("w", None, "identity/occurrence collapse: origin word not in frame")
        else:
            w_index = index("w", word_occurrence)

        glyph_occurrence = _first_glyph_occurrence(frame, origin_word_id)
        if glyph_occurrence is None:
            g_index = index("g", None, "no integer in stored E: no glyph occurrence")
        else:
            g_index = index("g", glyph_occurrence)

        add_entry(bundle, g_index, w_index, d_index)

    for definition_id in extra_definition_ids:
        record = corpus.definition(definition_id)
        origin_word_id = record.gonol.origin_word_id
        d_index = index("d", definition_id)
        word_occurrence = _first_word_occurrence(frame, origin_word_id)
        w_index = (
            index("w", word_occurrence)
            if word_occurrence is not None
            else index("w", None, "identity/occurrence collapse: origin word not in frame")
        )
        glyph_occurrence = _first_glyph_occurrence(frame, origin_word_id)
        g_index = (
            index("g", glyph_occurrence)
            if glyph_occurrence is not None
            else index("g", None, "no integer in stored E: no glyph occurrence")
        )
        entry = {
            "g": g_index,
            "w": w_index,
            "d": d_index,
            "map_id": "extra-definition",
            "fired": False,
        }
        entry["receipt_sha256"] = sha256(_canonical(entry)).hexdigest()
        entries.append(entry)

    for mode in MODES:
        axis_holes[mode] = sorted(holes[mode])

    return AdmissionCube(axes=axes, axis_holes=axis_holes, entries=tuple(entries))


def write_full_index_record(tensor: AdmissionCube, path: Path) -> Path:
    """Write the full-index record; this is the stored object, never a summary."""

    path = Path(path)
    path.write_bytes(tensor.bytes())
    return path


def read_full_index_record(data: bytes) -> AdmissionCube:
    """Read a full-index record and refuse anything contracted or partial."""

    if not isinstance(data, bytes):
        raise AdmissionCubeError("full-index record must be bytes")
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdmissionCubeError("full-index record is not valid canonical JSON") from exc
    if not isinstance(value, dict) or value.get("schema") != SCHEMA or value.get("version") != VERSION:
        raise AdmissionCubeError("full-index record schema or version mismatch")
    fields = {"schema", "version", "axes", "axis_holes", "entries", "hmmm"}
    if set(value) != fields or not isinstance(value["entries"], list):
        raise AdmissionCubeError("invalid full-index record fields")
    for field in ("axes", "axis_holes"):
        if not isinstance(value[field], dict) or set(value[field]) != set(MODES):
            raise AdmissionCubeError("full-index record is missing a tensor mode")
    for entry in value["entries"]:
        if not isinstance(entry, dict) or set(entry) != {*MODES, "map_id", "fired", "receipt_sha256"}:
            raise AdmissionCubeError("full-index entry fields do not match its modes")
        contents = {key: item for key, item in entry.items() if key != "receipt_sha256"}
        if sha256(_canonical(contents)).hexdigest() != entry["receipt_sha256"]:
            raise AdmissionCubeError("full-index entry receipt mismatch")
    tensor = AdmissionCube(
        axes=value["axes"],
        axis_holes=value["axis_holes"],
        entries=tuple(value["entries"]),
        hmmm=value.get("hmmm", _HMMM),
    )
    if _canonical(value) != data:
        raise AdmissionCubeError("full-index record does not replay byte-identically")
    return tensor


@dataclass(frozen=True)
class AdmissionWeights:
    """Candidate weights living on the cube: factors of the same modes only."""

    factors: dict[str, list[Any]]
    modes: tuple[str, ...] = MODES

    def __post_init__(self) -> None:
        if self.modes != MODES or set(self.factors) - set(MODES):
            raise AdmissionCubeError("weight factors must name only tensor modes")
        if "unnamed" in self.factors or any(
            not isinstance(name, str) or name not in MODES for name in self.factors
        ):
            raise AdmissionCubeError("no unnamed width; every weight factor names a tensor mode")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "version": VERSION,
            "factors": self.factors,
            "modes": list(self.modes),
            "standing": "candidate",
            "hmmm": _HMMM,
        }


def admission_cube_phone_card(tensor: AdmissionCube) -> dict[str, Any]:
    """A contracted phone card; only valid after the cube exists."""

    return tensor.contract()


__all__ = [
    "SCHEMA",
    "VERSION",
    "MODES",
    "HOLE",
    "_HMMM",
    "AdmissionCubeError",
    "AdmissionCube",
    "build_admission_cube",
    "write_full_index_record",
    "read_full_index_record",
    "AdmissionWeights",
    "admission_cube_phone_card",
]
