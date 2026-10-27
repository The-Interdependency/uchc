# ratios: loc_comments=234:76 imports_exports=8:5 calls_definitions=72:13
# SPDX-License-Identifier: FSL-1.1-ALv2
# Copyright 2026 Erin Spencer
# === MODULE_BUILD ===
# id: uchc_english_ordinal_ucns_consumer
#   module_name: ordinal_construction
#   module_kind: adapter
#   summary: exact glyph instantiation from the UCNS Public Gonol carrier and ordinal-affixiation geometry
#   owner: Erin Spencer
#   public_surface: construct_glyph_gonol, geometry_record, OrdinalStructuralField, OrdinalGeometryError
#   internal_surface: pinned UCNS module integrity and exact corpus receipts
#   auth_boundary: pinned UCNS source bytes and immutable Public Gonol arrangement
#   storage_boundary: verified structural corpus read-only; geometric records returned without DB mutation
#   network_boundary: none
#   user_data_boundary: caller source remains in local computation
#   admin_only: false
#   tests: ordinal_tests/test_ordinal_construction.py in Stack; tests/test_ordinal_construction.py in UCHC; paired complete-corpus acceptance
#   rollout: extract the verified Stack candidate; historical StructuralField receipts remain immutable
#   rollback: remove consumer module and its explicit API; do not modify UCNS or sealed corpus artifacts
#   requires: ucns.ordinal_affixiation, ucns.public_gonol, english_gonol.structural_query
#   since: 2026-10-19
#   unresolved: non-Public-Gonol scalar angles and higher-scale word-carrier angular attachment
# === END MODULE_BUILD ===
#
# === CONTRACTS ===
# id: uchc_ordinal_ucns_is_the_sole_geometry_authority
#   given: any UCHC glyph construction
#   then: it uses exact pinned UCNS Carrier, Participant and affixiate objects with no local angular or radial formula
#   class: correctness
#
# id: uchc_ordinal_glyph_occurrences_preserve_geometry
#   given: an ordered sequence of admitted Public Gonol glyphs
#   then: every occurrence preserves UCNS turn, exact halving exponent, multiplicity, order and replay receipt
#   class: correctness
#
# id: uchc_ordinal_no_fabricated_angles
#   given: an unadmitted glyph, changed UCNS producer, or unverified corpus origin
#   then: geometric construction refuses without allocating a replacement angle or changing corpus evidence
#   class: safety
#
# id: uchc_ordinal_query_consumes_verified_word_interiors
#   given: an admitted verified English structural query and Public Gonol glyphs
#   then: returned glyph geometry and each word's recoverable interior come from UCNS without inventing a parent word carrier
#   class: correctness
#
# id: uchc_ordinal_detached_interiors_keep_authority
#   given: a word or partial SPACE-seam result is detached from its query
#   then: every constructed word interior carries the exact UCNS repository, commit and source blob identities
#   class: evidence
# === END CONTRACTS ===

"""Stack-forged English ordinal candidate, consuming UCNS geometry.

Usage with exact UCNS producer installed:
    python -m english_gonol.ordinal_construction word

Use OrdinalStructuralField for a verified English corpus. The older
StructuralField remains the immutable historical-replay surface.
Stack owns this candidate until domain graduation. UCHC verifies its exact
extraction; see the ordinal work graph and extraction receipt before editing.
The Public Gonol fixes angular ordering; UCNS computes turns, radial halvings,
closure and receipts. Hyperspace before instantiation is NOT a gonol.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
from hashlib import sha1
import importlib
import json
from pathlib import Path

from english_gonol.structural_query import StructuralField

SCHEMA = "uchc.english-ordinal-geometry"
VERSION = "1.0.0"
UCNS_COMMIT = "ed0b0760f05cd975a7a811f8abeb70a11d09f00b"
UCNS_ORDINAL_BLOB = "9fa84ef20f19fe0c04df680f49b50ea307e6d624"
UCNS_PUBLIC_BLOB = "c1955e46e2dc918fb657cb346e42106d71937e91"
PUBLIC_GONOL_SHA256 = "55d10c84529a4d7bc7714786357e977b68d9df2ac3f73d20e229580b552c2ef5"


class OrdinalGeometryError(ValueError):
    """Named refusal rather than a local substitute for UCNS geometry."""

    def __init__(self, code: str, glyphs: tuple[str, ...] = ()):
        self.code = code
        self.glyphs = glyphs
        super().__init__(code)


def _git_blob_sha1(source: bytes) -> str:
    """Verify exact Git blob bytes; a digest is integrity, not authentication."""
    return sha1(b"blob " + str(len(source)).encode("ascii") + b"\0" + source).hexdigest()


@lru_cache(maxsize=1)
def _ucns():
    """Load the exact UCNS producer before admitting any geometric construction."""
    try:
        ordinal = importlib.import_module("ucns.ordinal_affixiation")
        public = importlib.import_module("ucns.public_gonol")
    except ImportError as exc:
        raise OrdinalGeometryError("UCNS_ORDINAL_PRODUCER_REQUIRED") from exc
    for module, expected in (
        (ordinal, UCNS_ORDINAL_BLOB),
        (public, UCNS_PUBLIC_BLOB),
    ):
        path = getattr(module, "__file__", None)
        if not path or not Path(path).is_file():
            raise OrdinalGeometryError("UCNS_PRODUCER_SOURCE_UNAVAILABLE")
        if _git_blob_sha1(Path(path).read_bytes()) != expected:
            raise OrdinalGeometryError("UCNS_PRODUCER_DRIFT")
    if (
        public.PUBLIC_GONOL_SHA256 != PUBLIC_GONOL_SHA256
        or public.public_gonol_sha256() != PUBLIC_GONOL_SHA256
        or len(public.PUBLIC_GONOL_157) != 157
        or public.PUBLIC_GONOL_157[0] != " "
    ):
        raise OrdinalGeometryError("PUBLIC_GONOL_CARRIER_DRIFT")
    carrier = ordinal.Carrier(
        tuple(public.PUBLIC_GONOL_157),
        "ucns:public-gonol-157:" + PUBLIC_GONOL_SHA256,
    )
    return ordinal, public, carrier


def construct_glyph_gonol(text: str, *, source: str = "uchc:english.ordinal/1"):
    """Construct every glyph instance through UCNS with exact local-frame placement.

    All glyphs must have positions on the pinned Public Gonol. In particular,
    an unknown Unicode scalar cannot be silently assigned a Unicode-order,
    hash-derived or locally invented bearing.
    """
    if not isinstance(text, str) or not text:
        raise OrdinalGeometryError("NONEMPTY_GLYPH_SEQUENCE_REQUIRED")
    if any(0xD800 <= ord(glyph) <= 0xDFFF for glyph in text):
        raise OrdinalGeometryError("UNICODE_SCALAR_REQUIRED")
    if not isinstance(source, str) or not source:
        raise OrdinalGeometryError("SOURCE_IDENTITY_REQUIRED")
    # SPACE is the fixed reference and seam event, not a radial glyph instance.
    if " " in text:
        raise OrdinalGeometryError("SPACE_SEAM_REQUIRES_FRAME_ATTACHMENT")
    ordinal, public, carrier = _ucns()
    missing = tuple(dict.fromkeys(
        glyph for glyph in text if public.public_gonol_position(glyph) is None
    ))
    if missing:
        raise OrdinalGeometryError("PUBLIC_GONOL_ANGLE_UNAVAILABLE", missing)
    construction = ordinal.affixiate(
        text,
        tuple(ordinal.Participant.atom(carrier, glyph) for glyph in text),
        origin="SPACE",
        relation="english.ordinal/1:glyph-instantiation",
        source=source,
    )
    if construction.recover() != tuple(text):
        raise OrdinalGeometryError("UCNS_CONSTRUCTION_RECOVERY_MISMATCH")
    return construction


def geometry_record(construction) -> dict:
    """Carry only Public Gonol glyph constructions, not arbitrary UCNS frames."""
    ordinal, _public, carrier = _ucns()
    if not isinstance(construction, ordinal.Construction):
        raise OrdinalGeometryError("UCNS_CONSTRUCTION_REQUIRED")
    if (
        construction.origin != "SPACE"
        or construction.relation != "english.ordinal/1:glyph-instantiation"
        or not construction.participants
        or any(
            participant.interior is not None
            or participant.carrier != carrier
            or participant.identity == " "
            for participant in construction.participants
        )
        or construction.identity != "".join(p.identity for p in construction.participants)
        or construction.recover() != tuple(construction.identity)
    ):
        raise OrdinalGeometryError("UCNS_PUBLIC_GLYPH_CONSTRUCTION_REQUIRED")
    # A native UCNS object can be built using an alternate relation or carrier.
    # Never attach Public Gonol provenance to that different construction.
    rebuilt = ordinal.affixiate(
        construction.identity, construction.participants,
        origin=construction.origin, relation=construction.relation,
        source=construction.source,
    )
    if construction.receipt != rebuilt.receipt:
        raise OrdinalGeometryError("UCNS_CONSTRUCTION_RECEIPT_MISMATCH")
    return {
        "schema": SCHEMA,
        "version": VERSION,
        "geometry_authority": {
            "repository": "The-Interdependency/ucns",
            "commit": UCNS_COMMIT,
            "ordinal_blob": UCNS_ORDINAL_BLOB,
            "public_gonol_blob": UCNS_PUBLIC_BLOB,
            "public_gonol_sha256": PUBLIC_GONOL_SHA256,
        },
        "construction": construction.record(),
        "receipt": construction.receipt,
        "recovered_glyphs": list(construction.recover()),
    }


def _refusal(code: str, glyphs: tuple[str, ...] = ()) -> dict:
    return {
        "standing": "refused",
        "code": code,
        "unplaced_glyphs": list(glyphs),
        "edges": [],
    }


class OrdinalStructuralField(StructuralField):
    """Verified structural English field using the selected UCNS glyph geometry.

    Preserves the historical structural artifact and its replay byte-for-byte.
    Only a verified complete corpus can bind its glyph identifiers to the
    canonical Public Gonol; partial fixtures cannot claim that binding.
    """

    def _word_geometry(self, surface: str, word: dict):
        if not self.complete_corpus:
            raise OrdinalGeometryError("COMPLETE_CORPUS_REQUIRED_FOR_PUBLIC_GONOL")
        return construct_glyph_gonol(
            surface,
            source=(
                "uchc:english.structural/1:"
                + self.manifest["receipt_sha256"]
                + ":word:"
                + str(word["word_id"])
            ),
        )

    def word(self, surface: str) -> dict:
        result = super().word(surface)
        constructed = self._word_geometry(surface, result)
        geometry = geometry_record(constructed)
        result["gonal_order"] = geometry["construction"]
        result["geometry_receipt"] = geometry["receipt"]
        result["geometry_authority"] = geometry["geometry_authority"]
        result["geometry_state"] = "constructed"
        return result

    def geometry(self, record: dict, *, operation: str) -> dict:
        if operation != "ordinal-affixiation":
            return super().geometry(record, operation=operation)
        graph = self.replay(record)
        if not self.complete_corpus:
            return _refusal("COMPLETE_CORPUS_REQUIRED_FOR_PUBLIC_GONOL")
        if graph["refusals"]:
            return _refusal("PARTICIPANT_ADMISSION_REQUIRED")
        if not graph["source"]:
            return _refusal("NONEMPTY_GLYPH_SEQUENCE_REQUIRED")
        try:
            interiors: dict[str, dict] = {}
            word_order = []
            for part in graph["parts"]:
                if part["kind"] != "word":
                    continue
                surface = graph["source"][part["start"]:part["end"]]
                key = str(part["identity"])
                if key not in interiors:
                    interior = self.word(surface)
                    interiors[key] = {
                        "word_id": part["identity"],
                        "source": surface,
                        "construction": interior["gonal_order"],
                        "receipt": interior["geometry_receipt"],
                        "geometry_authority": interior["geometry_authority"],
                    }
                word_order.append({"ordinal": part["ordinal"], "word_id": part["identity"]})
            if " " in graph["source"]:
                return {
                    "standing": "partial",
                    "code": "SPACE_SEAM_FRAME_NOT_SELECTED",
                    "source_receipt": graph["receipt_sha256"],
                    "word_interiors": list(interiors.values()),
                    "ordered_word_references": word_order,
                    "word_sites": graph["word_sites"],
                    "higher_word_frame": "hmmm:WORD_CARRIER_ANGLE_NOT_SELECTED",
                    "edges": [],
                }
            glyph_frame = construct_glyph_gonol(
                graph["source"],
                source="uchc:english.structural-query:" + graph["receipt_sha256"],
            )
        except OrdinalGeometryError as exc:
            return _refusal(exc.code, exc.glyphs)
        return {
            "standing": "constructed",
            "operation": "ordinal-affixiation",
            "source_receipt": graph["receipt_sha256"],
            "glyph_frame": geometry_record(glyph_frame),
            "word_interiors": list(interiors.values()),
            "ordered_word_references": word_order,
            "higher_word_frame": "hmmm:WORD_CARRIER_ANGLE_NOT_SELECTED",
            "edges": [],
        }

    def compose(self, record: dict, *, relation: str) -> dict:
        result = super().compose(record, relation=relation)
        if result["standing"] != "logically-closed":
            return result
        geometry = self.geometry(record, operation="ordinal-affixiation")
        if geometry["standing"] != "constructed":
            result["geometry_state"] = "hmmm:" + geometry["code"]
            result["word_interiors"] = geometry.get("word_interiors", [])
            result["word_sites"] = geometry.get("word_sites", [])
            result["geometry_refusal"] = geometry
            return result
        result["geometry_state"] = "constructed-glyph-frame;higher-word-frame-hmmm"
        result["glyph_geometry"] = geometry["glyph_frame"]
        result["word_interiors"] = geometry["word_interiors"]
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text")
    parser.add_argument("--source", default="uchc:english.ordinal/1")
    parser.add_argument("--state-dir", help="verified complete structural corpus")
    args = parser.parse_args()
    try:
        if args.state_dir:
            with OrdinalStructuralField(args.state_dir) as field:
                record = field.geometry(
                    field.construct(args.text),
                    operation="ordinal-affixiation",
                )
        else:
            record = geometry_record(construct_glyph_gonol(args.text, source=args.source))
            record["standing"] = "constructed"
    except OrdinalGeometryError as exc:
        record = _refusal(exc.code, exc.glyphs)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if record["standing"] == "constructed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
# ratios: loc_comments=234:76 imports_exports=8:5 calls_definitions=72:13
