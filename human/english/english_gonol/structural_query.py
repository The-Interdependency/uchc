# ratios: loc_comments=179:35 imports_exports=9:2 calls_definitions=67:15
"""Read-only text construction, atomic word recovery and explicit refusals.

Usage: ``with StructuralField(path) as field: graph = field.construct(text)``.
``field.replay(graph)`` recomputes the entire query record, including decisions.
Logical closure never claims an executed UCNS displacement or motion operation.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
from types import MappingProxyType

from english_gonol.hyperspace_construct import (
    promote_word, attach_word_origin, attach_definition_frame, glyph_inventory,
)
from english_gonol.structural_construct import StructuralError, _verified_connection
from english_gonol.structural_rules import TERMINAL_CLOSERS, canonical, digest, segment

# === CONTRACTS ===
# id: structural_queries_do_not_admit
#   given: arbitrary text including unknown words or scalars
#   then: preserve input with local admission refusals and leave the field unchanged
# id: structural_atomic_recovery
#   given: a closed word participating in another construction
#   then: consume its word axis while ordered glyph interior, inventory-derived glyph axes and origin attachments remain recoverable
# id: structural_geometry_refuses
#   given: a request for unavailable UCNS displacement or a new relation
#   then: emit a named refusal without synthesizing an edge or operation
# id: structural_queries_keep_verified_snapshot
#   given: a verified field and external database writes or replacement
#   then: every query consumes the same verified read snapshot until the field is closed
# === END CONTRACTS ===


class StructuralField:
    """One verified field; close it or use a context manager after queries."""

    def __init__(self, out_dir: str | Path):
        self._snapshot = _verified_connection(out_dir)
        self.db, verified = self._snapshot.__enter__()
        try:
            self._manifest_bytes = canonical(verified)
            self._field_receipt = verified["receipt_sha256"]
            self._profile_sha256 = verified["metadata"]["profile_sha256"]
            self._complete_corpus = verified["metadata"]["complete_corpus"] is True
            self._abbreviations = tuple(verified["metadata"]["profile"]["abbreviations"])
            self.words = MappingProxyType(dict(self.db.execute("SELECT surface,id FROM words")))
            self.characters = MappingProxyType({s: (cid, pos) for cid, s, pos in self.db.execute("SELECT * FROM characters")})
            self._glyph_axes = MappingProxyType({scalar: glyph.axis_index
                                                for scalar, glyph in glyph_inventory(self.db).items()})
        except BaseException:
            self.close()
            raise

    @property
    def manifest(self) -> dict:
        """Return a detached JSON snapshot; caller edits cannot alter receipts."""
        return json.loads(self._manifest_bytes)

    @property
    def complete_corpus(self) -> bool:
        """True only for a verified complete pinned field; partial fixtures are False."""
        return self._complete_corpus

    @property
    def abbreviations(self) -> tuple[str, ...]:
        """Expose the verified immutable parser policy without a writable alias."""
        return self._abbreviations

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def close(self):
        self._snapshot.__exit__(None, None, None)

    def word(self, surface: str) -> dict:
        """Recover one existing closed word and the distinct glyph-axis set."""
        wid = self.words.get(surface)
        if wid is None:
            raise StructuralError("WORD_ADMISSION_REQUIRED")
        word, axis = promote_word(self.db, wid)
        return {**word.as_dict(), "origin": "O_W", "axis": axis,
                "glyph_origin": "O_G", "glyph_axis_set": sorted({self._glyph_axes[c] for c in word.surface}),
                "occurrence_count": len(word.glyph_ids), "closed": True,
                "attachment": attach_word_origin(word),
                "definition_attachment": attach_definition_frame(word),
                "gonal_order": "hmmm:UCNS_OPERATION_REQUIRED"}

    def definition(self, record_id: int) -> dict:
        """Recover both constituent topologies and separate definition succession."""
        row = self.db.execute("SELECT * FROM records WHERE id=? AND kind='definition'", (record_id,)).fetchone()
        if row is None:
            raise StructuralError("DEFINITION_NOT_ADMITTED")
        rid, _, text, owner, origin, ordinal, previous, provenance, state = row
        parts = []
        for n, kind, wid, cid, start, end, function in self.db.execute(
            "SELECT ordinal,kind,word_id,character_id,start_offset,end_offset,function FROM components WHERE record_id=? ORDER BY ordinal", (rid,)):
            parts.append({"ordinal": n, "kind": kind, "identity": wid if kind == "word" else cid,
                          "start": start, "end": end, "function": json.loads(function)})
        return {"record_id": rid, "text": text, "owner_record_id": owner,
                "origin": {"space": "O_D", "word_id": origin} if origin is not None else None,
                "origin_state": state, "parts": parts,
                "constituent_chain": [[n - 1, n] for n in range(1, len(parts))],
                "constituent_direct": [{"owner_word_id": origin, "owner_record_id": owner,
                                        "part": n, "standing": state} for n in range(len(parts))],
                "definition_succession": {"ordinal": ordinal, "previous": previous},
                "provenance": json.loads(provenance)}

    def construct(self, text: str, *, boundary_decisions: dict | None = None) -> dict:
        """Construct exact ordered participation without changing corpus admission.

        Decisions map scalar offsets (decimal strings) to {closed: bool,
        source: nonempty evidence reference}. They can resolve only ambiguous
        punctuation, and remain explicit caller-supplied evidence in the receipt.
        """
        decisions = deepcopy({} if boundary_decisions is None else boundary_decisions)
        if not isinstance(decisions, dict):
            raise StructuralError("boundary decisions must be a mapping")
        parts = segment(text, self.abbreviations)
        used = set()
        output, refusals, spaces = [], [], []
        site_open = False
        for n, part in enumerate(parts):
            function = {"roles": list(part.roles), "closure": part.closure, "group": part.group}
            key = str(part.start)
            if key in decisions:
                decision = decisions[key]
                if (part.closure != "hmmm" or not isinstance(decision, dict)
                    or set(decision) != {"closed", "source"} or type(decision["closed"]) is not bool
                    or not isinstance(decision["source"], str) or not decision["source"].strip()):
                    raise StructuralError("invalid boundary decision")
                if part.group is not None and part.end != part.group[1]:
                    raise StructuralError("group closure decision must attach to final scalar")
                used.add(key)
                function["closure"] = "closed" if decision["closed"] else "open"
                if decision["closed"]:
                    function["roles"].append("sentence-close")
                function["closure_evidence"] = decision["source"]
            if part.kind == "word":
                identifier = self.words.get(part.text)
                space = "O_W"
                site_open = False
                if identifier is None:
                    refusals.append({"code": "WORD_ADMISSION_REQUIRED", "part": n,
                                     "unknown_scalars": [c for c in part.text if c not in self.characters]})
            else:
                entry = self.characters.get(part.text)
                identifier = entry[0] if entry else None
                space = "O_G"
                if entry is None:
                    refusals.append({"code": "GLYPH_ADMISSION_REQUIRED", "part": n})
                if part.text == " ":
                    spaces.append({"offset": part.start, "event": "continue-site" if site_open else "open-site"})
                    site_open = True
            output.append({"ordinal": n, "kind": part.kind, "identity": identifier,
                           "origin": space, "start": part.start, "end": part.end,
                           "function": function, "standing": "admitted" if identifier is not None else "hmmm"})
        if set(decisions) != used:
            raise StructuralError("unused or invalid boundary decision offsets")
        closure = [{"part": p["ordinal"], "state": p["function"]["closure"]} for p in output
                   if p["kind"] == "character" and p["function"]["closure"] in {"hmmm", "closed", "open"}
                   and (p["function"]["group"] is None or p["end"] == p["function"]["group"][1])]
        result = {"schema": "english-gonol.structural-query", "version": "1.0.0",
                  "field_receipt": self._field_receipt,
                  "profile_sha256": self._profile_sha256,
                  "source": text, "boundary_decisions": decisions, "parts": output,
                  "word_sites": spaces, "next_word_site_open": site_open,
                  "closure": closure, "input_closed": True,
                  "logical_state": "closed" if not refusals else "hmmm",
                  "refusals": refusals, "geometry_state": "hmmm"}
        # JSON-shaped values make an exported receipt identical after decoding.
        result = json.loads(canonical(result))
        result["receipt_sha256"] = digest(result)
        return result

    def replay(self, record: dict) -> dict:
        if not isinstance(record, dict) or "source" not in record or "boundary_decisions" not in record:
            raise StructuralError("incomplete query receipt")
        expected = self.construct(record["source"], boundary_decisions=record["boundary_decisions"])
        if canonical(expected) != canonical(record):
            raise StructuralError("query replay mismatch")
        return expected

    def compose(self, record: dict, *, relation: str) -> dict:
        """Close only registered relations over admitted, already-closed parts."""
        graph = self.replay(record)
        refusal = None
        if relation not in {"ordered-text", "sentence"}:
            refusal = "RELATION_NOT_REGISTERED"
        elif not graph["parts"] or graph["refusals"]:
            refusal = "PARTICIPANT_ADMISSION_REQUIRED"
        elif relation == "sentence":
            parts = list(graph["parts"])
            while parts and "separator" in parts[-1]["function"]["roles"]:
                parts.pop()
            # Segment already licenses closure before these closing scalars.
            # Retain them as participants, but locate the terminal mark cluster
            # before them. Whitespace inside a cluster is not silently collapsed.
            while parts and graph["source"][parts[-1]["start"]:parts[-1]["end"]] in TERMINAL_CLOSERS:
                parts.pop()
            terminal = set()
            while parts and parts[-1]["function"]["closure"] == "closed":
                terminal.add(parts.pop()["ordinal"])
            if (not terminal or any(c["state"] == "hmmm"
                                    or (c["state"] == "closed" and c["part"] not in terminal)
                                    for c in graph["closure"])):
                refusal = "SENTENCE_CLOSURE_UNRESOLVED"
        if refusal:
            return {"standing": "refused", "code": refusal, "edges": []}
        return {"standing": "logically-closed", "relation": relation,
                "participants": [{"kind": p["kind"], "identity": p["identity"], "origin": p["origin"]}
                                 for p in graph["parts"]],
                "source_receipt": graph["receipt_sha256"],
                "geometry_state": "hmmm:UCNS_OPERATION_REQUIRED"}

    def geometry(self, record: dict, *, operation: str) -> dict:
        self.replay(record)
        return {"standing": "refused", "code": "UCNS_OPERATION_REQUIRED",
                "operation": operation, "edges": []}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir")
    parser.add_argument("text")
    args = parser.parse_args()
    with StructuralField(args.out_dir) as field:
        print(json.dumps(field.construct(args.text), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# ratios: loc_comments=179:35 imports_exports=9:2 calls_definitions=67:15
