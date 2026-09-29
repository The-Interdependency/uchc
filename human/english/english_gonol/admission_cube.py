# === MODULE_BUILD ===
# id: uchc_english_admission_cube
#   module_name: admission_cube
#   module_kind: candidate
#   summary: the admission cube - one cube whose modes ARE the construct axes g, w, d, tau, pi; every mode present in every stored object, missing modes are named holes
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, MODES, AdmissionCubeError, HOLE, AdmissionCube, build_admission_cube, write_full_index_record, read_full_index_record, AdmissionWeights, admission_cube_phone_card
#   internal_surface: full infer() consumption, named index spaces, circle-plus-cover tau, canonical full-index serialization
#   auth_boundary: none
#   storage_boundary: immutable records only; the full-index record is the stored object
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: tests.test_admission_cube
#   rollout: candidate admission cube; weights live on the same modes; no harmonic T, no attention, no growth
#   rollback: remove this module and its tests
#   requires: uchc_english_inference_input, uchc_english_inference_v0
#   since: 2026-09-28
#   unresolved: no low-rank success is declared; no axis is deletable without breaking the record
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: admission_cube_has_all_modes
#   given: a built cube
#   then: exactly the modes g, w, d, tau, pi are present in the axes and in every stored entry
#   class: correctness
# id: admission_cube_holes_are_named
#   given: a missing mode
#   then: the entry carries a named hole, never a dropped index
#   class: doctrine
# id: admission_cube_tau_is_circle_plus_cover
#   given: a tau mode value
#   then: the value is (cos 2πp/157, sin 2πp/157, epsilon), not a degree scalar
#   class: correctness
# id: admission_cube_flattening_forbidden
#   given: the stored object
#   then: the full-index record keeps named axes and five-mode entries; flattening happens only in a phone card after the cube exists
#   class: doctrine
# id: admission_cube_weights_share_modes
#   given: a weights candidate
#   then: every weight factor names only tensor modes and has no unnamed width
#   class: doctrine
# === END CONTRACTS ===
"""The admission cube.

Modes:
  g    glyph origin
  w    word origin
  d    definition origin
  tau  turn + Mobius frame, as circle plus cover (cos, sin, epsilon)
  pi   placement angle, radius, layer

Filled from the full admitted frame and unreduced definition_ids over the
full O x S x C receipts. Missing modes are named holes in the construct,
never dropped indices. Flattening is forbidden as representation; a phone
card may contract only after the cube exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any

from .inference_input import EnglishConstruct, InferenceFrame
from .inference_v0 import Bundle, infer

SCHEMA = "uchc.admission-cube-v0"
VERSION = "0.1.0"
MODES = ("g", "w", "d", "tau", "pi")
_MODULUS = 157
HOLE = "hole"

_HMMM = "if you can delete an index and the code still runs, you did not build the cube"


class AdmissionCubeError(ValueError):
    """Raised when the cube fails closed."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _frame_positive(frame: str) -> int:
    return 1 if frame == "positive-local-frame" else -1


def _phase_residue(phase_turns: str) -> int:
    return int(phase_turns.split("/")[0]) % _MODULUS


def _tau_value(phase_turns: str, frame: str) -> list[float]:
    p = _phase_residue(phase_turns)
    epsilon = _frame_positive(frame)
    return [
        round(math.cos(2 * math.pi * p / _MODULUS), 15),
        round(math.sin(2 * math.pi * p / _MODULUS), 15),
        epsilon,
    ]


def _pi_value(placement: dict[str, Any]) -> list[Any]:
    return [
        _phase_residue(placement["angle_turn"]),
        placement["radius"],
        placement["layer"],
    ]


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
    ucns_source_root: Path,
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

    def add_entry(bundle: Bundle, g: Any, w: Any, d: Any, tau: Any, pi: Any) -> None:
        entry = {
            "g": g,
            "w": w,
            "d": d,
            "tau": tau,
            "pi": pi,
            "map_id": bundle.map_id,
            "fired": bundle.receipts is not None,
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

        if bundle.receipts is not None:
            lifted = bundle.receipts["lifted_unset"]
            placement = bundle.receipts["placement"]
            tau_value = _tau_value(lifted["mobius"]["phase_turns"], lifted["mobius"]["frame"])
            pi_value = _pi_value(placement)
            tau_index = index("tau", tau_value)
            pi_index = index("pi", pi_value)
        else:
            reasons = [refusal.clause for refusal in bundle.refusals] or ["not determined"]
            tau_index = index("tau", None, "; ".join(reasons))
            pi_index = index("pi", None, "; ".join(reasons))

        add_entry(bundle, g_index, w_index, d_index, tau_index, pi_index)

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
            "tau": _hole("tau", "not determined: no bundle receipts"),
            "pi": _hole("pi", "not determined: no bundle receipts"),
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
    if value.get("schema") != SCHEMA or value.get("version") != VERSION:
        raise AdmissionCubeError("full-index record schema or version mismatch")
    if set(value.get("axes", {})) != set(MODES):
        raise AdmissionCubeError("full-index record is missing a tensor mode")
    for entry in value.get("entries", []):
        if set(entry) < {"g", "w", "d", "tau", "pi"}:
            raise AdmissionCubeError("full-index record has an entry missing a mode")
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
        if set(self.factors) - set(MODES):
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
