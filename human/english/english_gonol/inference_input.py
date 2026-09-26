# ratios: loc_comments=320:51 imports_exports=13:12 calls_definitions=134:35
"""Receipt-bound native language input, without invented neural geometry.

Usage: open EnglishConstruct(path, database_sha256=..., logical_receipt=...)
in a with block, resolve_text(text, source_id=...), then recover definitions
through definition(id). See docs/INFERENCE_INPUT.md for full-corpus acceptance.
"""
# === MODULE_BUILD ===
# id: uchc_english_inference_input
#   module_name: inference_input
#   module_kind: adapter
#   summary: preserves exact input occurrences and native language construction against a verified complete corpus
#   owner: Erin Spencer
#   public_surface: EnglishConstruct, InferenceFrame, AdmissionError, ConstructError
#   internal_surface: private verified query snapshot, source-owned native promotion
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: tests.test_inference_input
#   rollout: explicit receipt-bound reader; no neural readiness promotion
#   rollback: remove reader consumers and module; retain original construct
#   unresolved: sense selection, neural projection and inference operator
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: uchc_input_preserves_source
#   given: any valid Unicode input and verified construct
#   then: exact source order multiplicity and UTF-8 spans survive including unsupported input
#   class: correctness
# id: uchc_input_consumes_native_construction
#   given: an admitted glyph word or definition
#   then: native producer objects and all source definition/evidence references remain recoverable
#   class: correctness
# id: uchc_input_fails_closed
#   given: altered source bytes receipts records invalid input or a closed handle
#   then: the reader refuses rather than manufacturing a successful admission
#   class: safety
# === END CONTRACTS ===
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
import tempfile
from types import MappingProxyType
from typing import Iterator
import unicodedata

from .full_construct_run import (
    SCHEMA as CONSTRUCT_SCHEMA, VERSION as CONSTRUCT_VERSION,
    _assert_schema_boundary, _definition_runs, _logical_receipt,
)
from .hyperspace_construct import (
    DefinitionGonol, GlyphGonol, WordGonol, glyph_inventory,
    promote_definition, promote_word,
)

SCHEMA = "uchc.english.inference-input"
VERSION = "1.0.0"


class ConstructError(ValueError):
    """The supplied artifact or reader state cannot support this operation."""


class AdmissionError(ConstructError):
    """Exact source evidence includes something outside the admitted construct."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _text(value: str, label: str, *, nonempty: bool = False) -> str:
    if type(value) is not str:
        raise TypeError(f"{label} must be str, without coercion")
    if nonempty and not value:
        raise ConstructError(f"{label} must be nonempty")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ConstructError(f"{label} contains a non-scalar surrogate") from exc
    return value


def _digest(value: str, label: str) -> str:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ConstructError(f"{label} must be a lowercase SHA-256 identity")
    return value


def _id(value: int) -> int:
    if type(value) is not int or value <= 0:
        raise ConstructError("identity must be a positive integer, not a coerced number")
    return value


@dataclass(frozen=True)
class ConstructIdentity:
    database_sha256: str
    logical_receipt: str
    metadata: tuple[tuple[str, str], ...]
    unicode_version: str


@dataclass(frozen=True)
class GlyphOccurrence:
    ordinal: int
    scalar: str
    utf8_start: int
    utf8_end: int
    character_id: int | None
    gonol: GlyphGonol | None


@dataclass(frozen=True)
class TextOccurrence:
    ordinal: int
    kind: str
    surface: str
    start: int
    end: int
    utf8_start: int
    utf8_end: int
    identity_id: int | None


@dataclass(frozen=True)
class WordRecord:
    construct_receipt: str
    gonol: WordGonol
    definition_ids: tuple[int, ...]


@dataclass(frozen=True)
class DefinitionComponent:
    ordinal: int
    kind: str
    identity_id: int
    start: int
    end: int


@dataclass(frozen=True)
class SemanticEvidence:
    status: str
    evidence_id: int
    source_ordinal: int
    channel: str
    relation: str
    target_word_id: int | None
    target_ref: str


@dataclass(frozen=True)
class DefinitionRecord:
    construct_receipt: str
    gonol: DefinitionGonol
    part_of_speech: str
    sense_id: str
    synset_id: str
    definition_index: int
    text: str
    previous_definition_id: int | None
    components: tuple[DefinitionComponent, ...]
    evidence: tuple[SemanticEvidence, ...]


@dataclass(frozen=True)
class InferenceFrame:
    """Input dossier, not a new gonol, sense decision or neural inference."""
    construct: ConstructIdentity
    source_id: str
    text: str
    glyphs: tuple[GlyphOccurrence, ...]
    occurrences: tuple[TextOccurrence, ...]
    words: tuple[WordRecord, ...]

    @property
    def glyphs_admitted(self) -> bool:
        return all(item.gonol is not None for item in self.glyphs)

    @property
    def words_admitted(self) -> bool:
        return all(item.identity_id is not None for item in self.occurrences)

    def require_complete(self) -> InferenceFrame:
        if not self.glyphs_admitted or not self.words_admitted:
            raise AdmissionError("source contains unadmitted glyphs or exact word surfaces")
        return self

    def recover_utf8(self) -> bytes:
        return "".join(item.scalar for item in self.glyphs).encode("utf-8")

    def to_dict(self) -> dict:
        shared = {}
        glyph_occurrences = []
        for item in self.glyphs:
            if item.gonol is not None:
                shared.setdefault(item.character_id, asdict(item.gonol))
            occurrence = asdict(item)
            occurrence.pop("gonol")
            glyph_occurrences.append(occurrence)
        payload = {
            "schema": SCHEMA, "version": VERSION,
            "construct": asdict(self.construct), "source_id": self.source_id,
            "text": self.text,
            "glyphs": [{"character_id": key, "gonol": value}
                       for key, value in shared.items()],
            "glyph_occurrences": glyph_occurrences,
            "occurrences": [asdict(item) for item in self.occurrences],
            "words": [asdict(item) for item in self.words],
            "glyphs_admitted": self.glyphs_admitted,
            "words_admitted": self.words_admitted,
            "sense_selection": "unresolved; every definition remains a candidate",
        }
        # JSON-native containers prevent tuple/list transport ambiguities.
        payload = json.loads(_canonical(payload))
        payload["receipt_sha256"] = sha256(_canonical(payload)).hexdigest()
        return payload

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())


class EnglishConstruct:
    """Verified, isolated query handle. Close it to release its temporary copy.

    Expected identities must come from the caller's trusted evidence/release
    record, not be accepted from an unverified companion manifest. One complete
    logical replay and index creation occur on open, never per inference turn.
    """

    def __init__(self, database: str | Path, *, database_sha256: str,
                 logical_receipt: str, snapshot_parent: str | Path | None = None):
        database_sha256 = _digest(database_sha256, "database_sha256")
        logical_receipt = _digest(logical_receipt, "logical_receipt")
        self._db: sqlite3.Connection | None = None
        self._temporary = tempfile.TemporaryDirectory(
            prefix="uchc-query-", dir=snapshot_parent)
        try:
            source = Path(database)
            target = Path(self._temporary.name) / "construct.db"
            # The same streamed bytes are copied and hashed; pathname replacement
            # cannot swap the reader's data after its identity was checked.
            with source.open("rb") as incoming, target.open("xb") as outgoing:
                digest = sha256()
                while chunk := incoming.read(1024 * 1024):
                    digest.update(chunk)
                    outgoing.write(chunk)
            if digest.hexdigest() != database_sha256:
                raise ConstructError("database byte identity mismatch")
            db = sqlite3.connect(target)
            self._db = db
            db.execute("PRAGMA trusted_schema=OFF")
            _assert_schema_boundary(db)
            if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ConstructError("SQLite integrity check failed")
            if db.execute("PRAGMA foreign_key_check").fetchall():
                raise ConstructError("construct has dangling references")
            metadata = dict(db.execute("SELECT key, value FROM meta"))
            if (metadata.get("schema"), metadata.get("version")) != (
                    CONSTRUCT_SCHEMA, CONSTRUCT_VERSION):
                raise ConstructError("unsupported construct schema/version")
            if _logical_receipt(db) != logical_receipt:
                raise ConstructError("complete logical receipt mismatch")
            self.identity = ConstructIdentity(database_sha256, logical_receipt,
                tuple(sorted(metadata.items())), unicodedata.unidata_version)
            # Read acceleration only; source rows and the source artifact are
            # unchanged. These private indexes do not define a new construction.
            db.execute("CREATE INDEX IF NOT EXISTS uchc_reader_semantic_definition "
                       "ON semantic_evidence(definition_id, id)")
            db.execute("CREATE INDEX IF NOT EXISTS uchc_reader_unresolved_definition "
                       "ON unresolved_semantic_evidence(definition_id, id)")
            db.commit()
            db.execute("PRAGMA query_only=ON")
            self.inventory = MappingProxyType(glyph_inventory(db))
            self._characters = dict(db.execute("SELECT scalar, id FROM characters"))
            self._scalars = {value: key for key, value in self._characters.items()}
        except Exception as exc:
            self.close()
            if isinstance(exc, (ConstructError, TypeError)):
                raise
            raise ConstructError(f"cannot open verified construct: {exc}") from exc

    def __enter__(self) -> EnglishConstruct:
        self._connection()
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def close(self) -> None:
        if self._db is not None:
            self._db.close()
            self._db = None
        self._temporary.cleanup()

    def _connection(self) -> sqlite3.Connection:
        if self._db is None:
            raise ConstructError("construct handle is closed")
        return self._db

    def word(self, surface: str) -> WordRecord | None:
        _text(surface, "surface")
        row = self._connection().execute(
            "SELECT id FROM words WHERE surface=?", (surface,)).fetchone()
        return None if row is None else self.word_by_id(row[0])

    def word_by_id(self, word_id: int) -> WordRecord:
        db = self._connection()
        word, _axis = promote_word(db, _id(word_id))
        if "".join(self._scalars[i] for i in word.glyph_ids) != word.surface:
            raise ConstructError("word construction does not recover its surface")
        definitions = tuple(row[0] for row in db.execute(
            "SELECT id FROM definitions WHERE origin_word_id=? ORDER BY ordinal",
            (word_id,)))
        return WordRecord(self.identity.logical_receipt, word, definitions)

    def iter_words(self) -> Iterator[WordRecord]:
        for (word_id,) in self._connection().execute("SELECT id FROM words ORDER BY id"):
            yield self.word_by_id(word_id)

    def definition(self, definition_id: int) -> DefinitionRecord:
        db = self._connection()
        native, _axis = promote_definition(db, _id(definition_id))
        row = db.execute(
            "SELECT part_of_speech, sense_id, synset_id, definition_index, text, "
            "previous_definition_id FROM definitions WHERE id=?", (definition_id,)
        ).fetchone()
        components = tuple(DefinitionComponent(ordinal, kind,
            word_id if kind == "word" else character_id, start, end)
            for ordinal, kind, word_id, character_id, start, end in db.execute(
                "SELECT ordinal, kind, word_id, character_id, start_offset, end_offset "
                "FROM definition_components WHERE definition_id=? ORDER BY ordinal",
                (definition_id,)))
        evidence = tuple(SemanticEvidence("resolved", evidence_id, ordinal,
            channel, relation, target_id, target_ref)
            for evidence_id, ordinal, channel, relation, target_id, target_ref in db.execute(
                "SELECT id, source_ordinal, channel, relation, target_word_id, target_ref "
                "FROM semantic_evidence WHERE definition_id=? ORDER BY id", (definition_id,)))
        evidence += tuple(SemanticEvidence("unresolved", evidence_id, ordinal,
            channel, relation, None, target_ref)
            for evidence_id, ordinal, channel, relation, target_ref in db.execute(
                "SELECT id, source_ordinal, channel, relation, target_ref "
                "FROM unresolved_semantic_evidence WHERE definition_id=? ORDER BY id",
                (definition_id,)))
        return DefinitionRecord(self.identity.logical_receipt, native, *row, components, evidence)

    def iter_definitions(self) -> Iterator[DefinitionRecord]:
        for (definition_id,) in self._connection().execute(
                "SELECT id FROM definitions ORDER BY origin_word_id, ordinal"):
            yield self.definition(definition_id)

    def recover_definition(self, definition: DefinitionRecord) -> str:
        # Never trust a caller-constructed object or a record from another corpus.
        if type(definition) is not DefinitionRecord:
            raise ConstructError("expected a native definition record")
        original = self.definition(definition.gonol.definition_id)
        if _canonical(asdict(original)) != _canonical(asdict(definition)):
            raise ConstructError("definition record does not match this construct")
        parts = []
        end = 0
        for component in original.components:
            if component.start != end:
                raise ConstructError("definition component spans are not contiguous")
            value = (self._connection().execute("SELECT surface FROM words WHERE id=?",
                         (component.identity_id,)).fetchone()[0]
                     if component.kind == "word" else self._scalars[component.identity_id])
            if original.text[component.start:component.end] != value:
                raise ConstructError("definition component does not recover source span")
            parts.append(value)
            end = component.end
        recovered = "".join(parts)
        if recovered != original.text:
            raise ConstructError("definition source does not recover completely")
        return recovered

    def resolve_text(self, text: str, *, source_id: str) -> InferenceFrame:
        self._connection()
        _text(text, "text")
        _text(source_id, "source_id", nonempty=True)
        offsets = [0]
        glyphs = []
        for ordinal, scalar in enumerate(text):
            offsets.append(offsets[-1] + len(scalar.encode("utf-8")))
            glyphs.append(GlyphOccurrence(ordinal, scalar, offsets[-2], offsets[-1],
                self._characters.get(scalar), self.inventory.get(scalar)))
        words: dict[str, WordRecord | None] = {}
        occurrences = []
        for ordinal, (kind, surface, start, end) in enumerate(_definition_runs(text)):
            if kind == "word":
                if surface not in words:
                    words[surface] = self.word(surface)
                word = words[surface]
                identity_id = None if word is None else word.gonol.word_id
            else:
                identity_id = self._characters.get(surface)
            occurrences.append(TextOccurrence(ordinal, kind, surface, start, end,
                offsets[start], offsets[end], identity_id))
        return InferenceFrame(self.identity, source_id, text, tuple(glyphs),
                              tuple(occurrences), tuple(w for w in words.values() if w is not None))

    def resolve_utf8(self, data: bytes, *, source_id: str) -> InferenceFrame:
        if type(data) is not bytes:
            raise TypeError("data must be bytes")
        return self.resolve_text(data.decode("utf-8", errors="strict"), source_id=source_id)

    def replay(self, data: bytes) -> InferenceFrame:
        if type(data) is not bytes:
            raise TypeError("serialized frame must be canonical UTF-8 bytes")
        try:
            value = json.loads(data)
            frame = self.resolve_text(value["text"], source_id=value["source_id"])
            if frame.to_bytes() != data:
                raise ConstructError("frame does not replay byte-identically")
            return frame
        except (KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
            raise ConstructError("invalid serialized frame") from exc


__all__ = ["EnglishConstruct", "InferenceFrame", "ConstructIdentity", "ConstructError",
           "AdmissionError", "GlyphOccurrence", "TextOccurrence", "WordRecord",
           "DefinitionRecord", "DefinitionComponent", "SemanticEvidence"]
# ratios: loc_comments=320:51 imports_exports=13:12 calls_definitions=134:35
