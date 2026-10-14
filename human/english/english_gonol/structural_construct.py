# ratios: loc_comments=540:80 imports_exports=19:6 calls_definitions=333:23
"""Complete English structural construction and byte-stable replay.

Usage: python -m english_gonol.structural_construct build --source-root PATH
--ucns-source-root PATH --out-dir NEW_PATH; use ``verify NEW_PATH`` to replay.
The source/profile/producer identity is part of the graph, not a renderer flag.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from contextlib import closing, contextmanager, ExitStack
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import stat
import subprocess
import tempfile
from typing import Callable

from english_gonol.full_construct_run import (
    _load_verified_public_gonol, UCNS_PUBLIC_GONOL_COMMIT,
    UCNS_PUBLIC_GONOL_MODULE_SHA256, PUBLIC_GONOL_SHA256,
)
from english_gonol.language.source import (
    WordnetSnapshot, load_oewn_2025, OEWN_COMMIT, OEWN_REPOSITORY,
)
from english_gonol.structural_rules import (
    DEFAULT_ABBREVIATIONS, PROFILE, canonical, digest, policy, segment,
)

# === MODULE_BUILD ===
# id: english_structural_profile
#   module_name: structural_construct
#   module_kind: engine
#   summary: complete source-bound structural admission with shared identities, exact participation, local closure and replay
#   owner: Erin Spencer
#   public_surface: build, run, verify, main
#   internal_surface: normalized source constructions and canonical rows
#   auth_boundary: read-only pinned corpus and UCNS producer
#   storage_boundary: writes one new caller-selected output directory
#   network_boundary: none
#   user_data_boundary: none; text-query state remains caller-owned
#   admin_only: false
#   tests: tests/test_structural_profile.py
#   rollout: explicit structural profile; sealed v2 receipts remain historical
#   rollback: remove new profile output; never silently downgrade consumers
#   unresolved: UCNS displacement and multiword definition origin attachment
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: structural_shared_atomic_words
#   given: the complete declared corpus
#   then: exact words and scalars share identities and ordered references preserve multiplicity
# id: structural_definitions_and_origins
#   given: source definitions and lexical entries
#   then: preserve constituent direct/chain relations, definition succession and explicit unresolved compound origins
# id: structural_complete_replay
#   given: a materialized structural field
#   then: reconstruct every source text and verify canonical graph/evidence bytes, policy, counts and receipt in one stable read transaction
# id: structural_complete_raw_source
#   given: complete-corpus standing is requested or replayed
#   then: independently bind every raw source byte and relative filename to the pinned tree without trusting reduced snapshot claims
# id: structural_partial_carrier_refusal
#   given: a partial snapshot-only field
#   then: refuse every carrier position at build and replay; only complete pinned fields expose UCNS carrier axes
# id: structural_standalone_database
#   given: a sealed construct.db with WAL, SHM or rollback-journal sidecars, or WAL file format
#   then: refuse verification so the sealed file bytes alone carry the verified state
# id: structural_partial_source_identity
#   given: a partial snapshot-only build
#   then: record a null source commit; only complete pinned builds claim the OEWN commit
# id: structural_regular_database
#   given: construct.db is a symlink or other nonregular file
#   then: refuse verification before opening it
# === END CONTRACTS ===

SCHEMA = "english-gonol.structural-construct"
VERSION = "1.1.0"
# Derived from the clean pinned OEWN checkout using this source loader. The
# ordered digest covers every included field, including unused relation evidence.
PINNED_SOURCE = {
    "repository": OEWN_REPOSITORY, "commit": OEWN_COMMIT,
    "tree_sha256": "3a46546a1ffbb4aed98990535ad5155c69be12ad09fdf093701b257d2a3e468f",
    "files": 73, "lexemes": 135969, "synsets": 107519,
    "evidence_sha256": "42b18c16c786bad3801abf36e3f5966daba94df4b88792491ad22229749480d3",
}
# Exact upper bounds measured over the immutable pinned OEWN YAML tree.
# They bound raw reads/decoding; matching the pinned digest still grants identity.
RAW_SOURCE_MAX_FILES = 73
RAW_SOURCE_MAX_FILE_BYTES = 3333131
RAW_SOURCE_MAX_TOTAL_BYTES = 46372711
RAW_SOURCE_MAX_PATH_BYTES = 23
FIXED_METADATA = {
    "geometry_state": "hmmm", "normalization": "none",
    "definition_topologies": ["constituent-chain", "constituent-direct", "definition-succession"],
    "authority_transfer": False,
}
# Bind the entire project import-time closure, including package initialization.
# The fresh-process regression reconciles this inventory against loaded source files.
IMPLEMENTATION_FILES = (
    "structural_rules.py", "structural_construct.py", "structural_query.py",
    "hyperspace_construct.py", "full_construct_run.py", "language/source.py",
    "language/__init__.py", "language/affixes.py", "language/manifest.py",
    "language/model.py", "language/morphology.py", "language/relational_bridge.py",
    "language/rendering.py",
)
TABLES = ("meta", "characters", "words", "word_characters", "records", "components", "evidence")
SQL = """
PRAGMA foreign_keys=ON;
PRAGMA journal_mode=DELETE;
PRAGMA synchronous=FULL;
PRAGMA temp_store=MEMORY;
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE characters(id INTEGER PRIMARY KEY, scalar TEXT NOT NULL UNIQUE, public_position INTEGER);
CREATE TABLE words(id INTEGER PRIMARY KEY, surface TEXT NOT NULL UNIQUE);
CREATE TABLE word_characters(word_id INTEGER NOT NULL REFERENCES words(id),
 ordinal INTEGER NOT NULL, character_id INTEGER NOT NULL REFERENCES characters(id),
 PRIMARY KEY(word_id,ordinal)) WITHOUT ROWID;
CREATE TABLE records(id INTEGER PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('lexical','definition')),
 text TEXT NOT NULL, owner_record_id INTEGER REFERENCES records(id),
 origin_word_id INTEGER REFERENCES words(id), ordinal INTEGER NOT NULL,
 previous_definition_id INTEGER REFERENCES records(id), provenance TEXT NOT NULL,
 origin_state TEXT NOT NULL);
CREATE TABLE components(record_id INTEGER NOT NULL REFERENCES records(id), ordinal INTEGER NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('word','character')),
 word_id INTEGER REFERENCES words(id), character_id INTEGER REFERENCES characters(id),
 start_offset INTEGER NOT NULL, end_offset INTEGER NOT NULL, function TEXT NOT NULL,
 PRIMARY KEY(record_id,ordinal), CHECK((kind='word' AND word_id IS NOT NULL AND character_id IS NULL)
 OR (kind='character' AND character_id IS NOT NULL AND word_id IS NULL))) WITHOUT ROWID;
CREATE TABLE evidence(kind TEXT NOT NULL, ordinal INTEGER NOT NULL, payload TEXT NOT NULL,
 PRIMARY KEY(kind,ordinal)) WITHOUT ROWID;
CREATE INDEX records_owner ON records(owner_record_id,ordinal);
CREATE INDEX components_word ON components(word_id,record_id);
"""


class StructuralError(ValueError):
    """Malformed, incompatible or unverified structural artifact."""


def _encoded(value: object) -> str:
    return canonical(value).decode("utf-8")


def _implementation() -> str:
    root = Path(__file__).parent
    return digest({name: sha256((root / name).read_bytes()).hexdigest()
                   for name in IMPLEMENTATION_FILES})


def _receipt(db: sqlite3.Connection) -> str:
    result = sha256()
    for table in TABLES:
        # Tables and order are fixed by this module, never caller SQL.
        result.update(canonical(table) + b"\n")
        ordering = "1,2" if table in {"word_characters", "components", "evidence"} else "1"
        for row in db.execute(f"SELECT * FROM {table} ORDER BY {ordering}"):
            result.update(canonical(list(row)) + b"\n")
    return result.hexdigest()


def _manifest(db: sqlite3.Connection) -> dict:
    meta = {key: json.loads(value) for key, value in db.execute("SELECT key,value FROM meta")}
    return {"schema": SCHEMA, "version": VERSION, "construct_file": "construct.db",
            "metadata": meta, "counts": {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                                          for t in TABLES}, "receipt_sha256": _receipt(db)}


def _function(part) -> str:
    return _encoded({"roles": part.roles, "closure": part.closure, "group": part.group})


def _evidence_digest(rows) -> str:
    """Bind all ordered source evidence, not only fields used by construction."""
    result = sha256()
    for kind, ordinal, payload in rows:
        result.update(canonical([kind, ordinal, payload]) + b"\n")
    return result.hexdigest()


def _texts(snapshot: WordnetSnapshot) -> list[str]:
    """Every admitted lexical surface and definition text of one snapshot."""
    return ([s for lex in snapshot.lexemes for s in (lex.lemma, *lex.forms)]
            + [s for syn in snapshot.synsets for s in (*syn.members, *syn.definitions)])


def _raw_source_name(name: str) -> bytes:
    """Accept only canonical relative YAML names within the pinned path budget."""
    if (not isinstance(name, str) or not name or "/" in name or "\\" in name
        or any(ord(c) < 32 for c in name) or PurePosixPath(name).is_absolute()
        or name != PurePosixPath(name).as_posix() or ".." in PurePosixPath(name).parts
        or not name.endswith(".yaml")):
        raise StructuralError("invalid raw source path")
    encoded = name.encode("utf-8")
    if len(encoded) > RAW_SOURCE_MAX_PATH_BYTES:
        raise StructuralError("raw source path exceeds pinned resource limit")
    return encoded


def _raw_tree_update(result, name: str, data: bytes) -> None:
    """Use exactly language.source._source_tree_digest's length-prefixed bytes."""
    encoded = _raw_source_name(name)
    result.update(len(encoded).to_bytes(4, "big"))
    result.update(encoded)
    result.update(len(data).to_bytes(8, "big"))
    result.update(data)


def _raw_source_files(source_root: str | Path) -> tuple[Path, list[str]]:
    """Bound the pinned flat YAML directory and preflight sizes before reads."""
    if (not all(hasattr(os, flag) for flag in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK"))
        or os.open not in getattr(os, "supports_dir_fd", set())
        or os.scandir not in getattr(os, "supports_fd", set())):
        raise StructuralError("raw source filesystem build requires no-follow directory descriptor support")
    root = Path(source_root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise StructuralError("raw source root must be a nonsymlink directory")
    names, total = [], 0
    with ExitStack() as stack:
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        stack.callback(os.close, directory)
        with os.scandir(directory) as entries:
            for entry in entries:
                if len(names) >= RAW_SOURCE_MAX_FILES:
                    raise StructuralError("raw source exceeds pinned resource limits")
                if entry.is_symlink():
                    raise StructuralError("raw source symlinks are not admitted")
                if not entry.is_file(follow_symlinks=False) or not entry.name.endswith(".yaml"):
                    raise StructuralError("raw source requires only flat regular YAML files")
                _raw_source_name(entry.name)
                size = entry.stat(follow_symlinks=False).st_size
                total += size
                names.append(entry.name)
                if size > RAW_SOURCE_MAX_FILE_BYTES or total > RAW_SOURCE_MAX_TOTAL_BYTES:
                    raise StructuralError("raw source exceeds pinned resource limits")
    if len(names) != PINNED_SOURCE["files"]:
        raise StructuralError("raw source file count mismatch")
    return root, sorted(names)


def _read_raw_source(root: Path, name: str, limit: int) -> bytes:
    """Read through no-follow directory descriptors, including nested parents."""
    with ExitStack() as stack:
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        stack.callback(os.close, directory)
        parts = PurePosixPath(name).parts
        for part in parts[:-1]:
            directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            stack.callback(os.close, directory)
        with os.fdopen(os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory), "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise StructuralError("raw source descriptor must be a regular file")
            if info.st_size > limit:
                raise StructuralError("raw source exceeds pinned resource limits")
            data = stream.read(limit + 1)
    if len(data) > limit:
        raise StructuralError("raw source exceeds pinned resource limits")
    return data


def _embed_raw_source(db: sqlite3.Connection, source_root: str | Path) -> None:
    """Preserve all exact pinned YAML bytes; any mismatch discards the build."""
    root, names = _raw_source_files(source_root)
    result, total = sha256(), 0
    for ordinal, name in enumerate(names):
        data = _read_raw_source(root, name, min(RAW_SOURCE_MAX_FILE_BYTES, RAW_SOURCE_MAX_TOTAL_BYTES - total))
        total += len(data)
        _raw_tree_update(result, name, data)
        db.execute("INSERT INTO evidence VALUES('source-file',?,?)",
                   (ordinal, _encoded({"path": name, "base64": base64.b64encode(data).decode("ascii")})))
    if result.hexdigest() != PINNED_SOURCE["tree_sha256"]:
        raise StructuralError("raw source tree digest mismatch")


def _verify_raw_source(db: sqlite3.Connection, complete: bool) -> int:
    """Bound SQL payload sizes before fetching, then stream exact raw recovery."""
    count, largest, encoded_total = db.execute(
        "SELECT COUNT(*),MAX(length(CAST(payload AS BLOB))),SUM(length(CAST(payload AS BLOB))) "
        "FROM evidence WHERE kind='source-file'").fetchone()
    if not complete:
        if count:
            raise StructuralError("partial corpus cannot claim raw source evidence")
        return 0
    if count != PINNED_SOURCE["files"] or count > RAW_SOURCE_MAX_FILES:
        raise StructuralError("raw source file count mismatch")
    overhead = 6 * RAW_SOURCE_MAX_PATH_BYTES + len(_encoded({"path": "", "base64": ""}))
    if (largest > 4 * ((RAW_SOURCE_MAX_FILE_BYTES + 2) // 3) + overhead
        or encoded_total > 4 * ((RAW_SOURCE_MAX_TOTAL_BYTES + 2) // 3) + count * (overhead + 4)):
        raise StructuralError("raw source payload exceeds pinned resource limits")
    result, total, previous = sha256(), 0, None
    for expected, (ordinal, payload) in enumerate(db.execute(
            "SELECT ordinal,payload FROM evidence WHERE kind='source-file' ORDER BY ordinal")):
        item = json.loads(payload)
        if payload != _encoded(item):
            raise StructuralError("noncanonical raw source payload")
        if not isinstance(item, dict) or set(item) != {"path", "base64"}:
            raise StructuralError("invalid raw source payload fields")
        name, encoded = item["path"], item["base64"]
        _raw_source_name(name)
        if ordinal != expected or (previous is not None and name <= previous):
            raise StructuralError("raw source order or duplicate path mismatch")
        if not isinstance(encoded, str) or len(encoded) > 4 * ((RAW_SOURCE_MAX_FILE_BYTES + 2) // 3):
            raise StructuralError("raw source base64 exceeds pinned resource limits")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise StructuralError("invalid raw source base64") from exc
        if base64.b64encode(data).decode("ascii") != encoded:
            raise StructuralError("noncanonical raw source base64")
        total += len(data)
        if len(data) > RAW_SOURCE_MAX_FILE_BYTES or total > RAW_SOURCE_MAX_TOTAL_BYTES:
            raise StructuralError("raw source exceeds pinned resource limits")
        _raw_tree_update(result, name, data)
        previous = name
    if result.hexdigest() != PINNED_SOURCE["tree_sha256"]:
        raise StructuralError("raw source tree digest mismatch")
    return count


def build(snapshot: WordnetSnapshot, *, out_dir: str | Path,
          public_position: Callable[[str], int | None], producer: dict,
          complete_corpus: bool = False, source_root: str | Path | None = None) -> dict:
    """Build all supplied source records. Production ``run`` verifies full pins.

    Snapshot-only builds remain partial. ``complete_corpus=True`` additionally
    requires ``source_root``: exact raw YAML bytes and the full reduced projection
    must independently match their pinned identities before completeness is granted.
    Fixture callbacks supply carrier observations only, without UCNS authority.
    """
    if type(complete_corpus) is not bool:
        raise StructuralError("complete_corpus must be boolean")
    # Only a complete, pinned build may claim the OEWN commit; partial snapshots record none.
    source = {"repository": OEWN_REPOSITORY, "commit": OEWN_COMMIT if complete_corpus else None,
              "tree_sha256": snapshot.source_tree_sha256,
              "files": snapshot.source_file_count,
              "lexemes": len(snapshot.lexemes), "synsets": len(snapshot.synsets),
              "evidence_sha256": _evidence_digest(
                  (kind, i, asdict(item))
                  for kind, items in (("lexeme", snapshot.lexemes), ("synset", snapshot.synsets))
                  for i, item in enumerate(items))}
    if complete_corpus and canonical(source) != canonical(PINNED_SOURCE):
        raise StructuralError("complete corpus requires exact pinned source evidence")
    if complete_corpus and source_root is None:
        raise StructuralError("complete corpus requires independent raw source")
    if source_root is not None and not complete_corpus:
        raise StructuralError("raw source requires an explicit complete corpus request")
    if not complete_corpus and any(public_position(c) is not None
                                   for c in {c for t in _texts(snapshot) for c in t}):
        raise StructuralError("partial build refuses carrier positions before writing")
    output = Path(out_dir).resolve()
    if output.exists():
        raise StructuralError("output already exists; use a new directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".structural-", dir=output.parent))
    db = sqlite3.connect(stage / "construct.db")
    try:
        db.executescript(SQL)
        if complete_corpus:
            _embed_raw_source(db, source_root)
        lexical = sorted({s for lex in snapshot.lexemes for s in (lex.lemma, *lex.forms)} |
                         {s for syn in snapshot.synsets for s in syn.members})
        abbreviations = sorted(set(DEFAULT_ABBREVIATIONS) |
                               {s[:-1] for s in lexical if s.endswith(".") and s[:-1].isalpha()})
        admission_policy = policy(abbreviations)
        meta = {"profile": admission_policy, "profile_sha256": digest(admission_policy),
                "source": source,
                "complete_corpus": complete_corpus, "producer": producer,
                "implementation_sha256": _implementation(),
                **FIXED_METADATA}
        db.executemany("INSERT INTO meta VALUES(?,?)", ((k, _encoded(v)) for k, v in sorted(meta.items())))
        texts = lexical + [text for syn in snapshot.synsets for text in syn.definitions]
        scalars = sorted({c for text in texts for c in text}, key=ord)
        surfaces = sorted({p.text for text in texts for p in segment(text, abbreviations) if p.kind == "word"})
        character_ids = {c: i for i, c in enumerate(scalars, 1)}
        word_ids = {w: i for i, w in enumerate(surfaces, 1)}
        db.executemany("INSERT INTO characters VALUES(?,?,?)",
                       ((i, c, public_position(c)) for c, i in character_ids.items()))
        db.executemany("INSERT INTO words VALUES(?,?)", ((i, w) for w, i in word_ids.items()))
        db.executemany("INSERT INTO word_characters VALUES(?,?,?)",
                       ((wid, j, character_ids[c]) for w, wid in word_ids.items() for j, c in enumerate(w)))
        for kind, items in (("lexeme", snapshot.lexemes), ("synset", snapshot.synsets)):
            db.executemany("INSERT INTO evidence VALUES(?,?,?)",
                           ((kind, i, _encoded(asdict(item))) for i, item in enumerate(items)))
        record_id = 0

        def add_record(kind, text, owner, origin, ordinal, previous, provenance):
            nonlocal record_id
            record_id += 1
            rid = record_id
            state = "attached" if origin is not None else "hmmm:compound-lexical-origin"
            db.execute("INSERT INTO records VALUES(?,?,?,?,?,?,?,?,?)",
                       (rid, kind, text, owner, origin, ordinal, previous, _encoded(provenance), state))
            db.executemany("INSERT INTO components VALUES(?,?,?,?,?,?,?,?)", (
                (rid, j, p.kind, word_ids[p.text] if p.kind == "word" else None,
                 character_ids[p.text] if p.kind == "character" else None,
                 p.start, p.end, _function(p)) for j, p in enumerate(segment(text, abbreviations))))
            return rid

        entry_ids = {s: add_record("lexical", s, None, word_ids.get(s), i, None,
                                   {"source": "corpus-lexical-membership"}) for i, s in enumerate(lexical)}
        synsets = snapshot.synset_map()
        ordinals: dict[str, int] = {}
        previous: dict[str, int] = {}
        for li, lexeme in enumerate(snapshot.lexemes):
            for si, sense in enumerate(lexeme.senses):
                if sense.synset_id not in synsets:
                    raise StructuralError(f"missing synset: {sense.synset_id}")
                for di, text in enumerate(synsets[sense.synset_id].definitions):
                    ordinal = ordinals.get(lexeme.lemma, 0)
                    rid = add_record("definition", text, entry_ids[lexeme.lemma], word_ids.get(lexeme.lemma),
                                     ordinal, previous.get(lexeme.lemma),
                                     {"lexeme_ordinal": li, "sense_ordinal": si, "definition_index": di,
                                      "sense_id": sense.sense_id, "synset_id": sense.synset_id,
                                      "part_of_speech": lexeme.part_of_speech})
                    previous[lexeme.lemma] = rid
                    ordinals[lexeme.lemma] = ordinal + 1
        db.commit()
        integrity = db.execute("PRAGMA integrity_check").fetchall()
        if integrity != [("ok",)]:
            raise StructuralError(f"post-build integrity failure: {integrity[:10]}")
        manifest = _manifest(db)
        (stage / "manifest.json").write_bytes(canonical(manifest) + b"\n")
        db.close()
        verify(stage)
        stage.rename(output)
        return manifest
    except BaseException:
        db.close()
        shutil.rmtree(stage, ignore_errors=True)
        raise


SIDECARS = ("-wal", "-shm", "-journal")


def open_readonly(path: str | Path) -> sqlite3.Connection:
    """Open one standalone rollback-journal database; sidecar state is refused."""
    try:
        mode = os.lstat(path).st_mode
    except OSError as exc:
        raise StructuralError("database must be a regular file") from exc
    if not stat.S_ISREG(mode):
        raise StructuralError("database must be a regular nonsymlink file")
    path = Path(path).resolve()
    if any(Path(str(path) + suffix).exists() for suffix in SIDECARS):
        raise StructuralError("database sidecar files are not part of the sealed artifact")
    with path.open("rb") as stream:
        header = stream.read(20)
    if len(header) < 20 or header[18:20] != b"\x01\x01":
        raise StructuralError("database must use rollback journal format, not WAL")
    return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)


def _schema(db: sqlite3.Connection) -> list:
    """Bind tables, columns, constraints, indexes and absence of extra objects."""
    return db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master "
                      "WHERE name NOT GLOB 'sqlite_*' ORDER BY type,name").fetchall()


@contextmanager
def _verified_connection(out_dir: str | Path):
    """Keep verification and subsequent reads on one snapshot until closed."""
    root = Path(out_dir)
    manifest_bytes = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest_bytes != canonical(manifest) + b"\n":
        raise StructuralError("noncanonical manifest encoding")
    if (manifest.get("schema"), manifest.get("version")) != (SCHEMA, VERSION):
        raise StructuralError("schema/version mismatch")
    with closing(open_readonly(root / "construct.db")) as db:
        db.execute("BEGIN")
        with closing(sqlite3.connect(":memory:")) as expected:
            expected.executescript(SQL)
            if _schema(db) != _schema(expected):
                raise StructuralError("database schema mismatch")
        if db.execute("PRAGMA journal_mode").fetchone() != ("delete",) or any(
                Path(str((root / "construct.db").resolve()) + suffix).exists() for suffix in SIDECARS):
            raise StructuralError("database sidecar files are not part of the sealed artifact")
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables != set(TABLES):
            raise StructuralError("table set mismatch")
        if db.execute("PRAGMA integrity_check").fetchone() != ("ok",) or db.execute("PRAGMA foreign_key_check").fetchone():
            raise StructuralError("database integrity failure")
        for _key, value in db.execute("SELECT key,value FROM meta"):
            if value != _encoded(json.loads(value)):
                raise StructuralError("noncanonical metadata payload")
        meta = manifest["metadata"]
        expected_keys = set(FIXED_METADATA) | {
            "profile", "profile_sha256", "source", "complete_corpus", "producer", "implementation_sha256"}
        if (set(meta) != expected_keys
            or any(canonical(meta.get(k)) != canonical(v) for k, v in FIXED_METADATA.items())
            or type(meta.get("complete_corpus")) is not bool):
            raise StructuralError("fixed metadata boundary mismatch")
        source = meta["source"]
        if (set(source) != set(PINNED_SOURCE)
            or source["repository"] != OEWN_REPOSITORY or source["commit"] != (OEWN_COMMIT if meta["complete_corpus"] else None)
            or (meta["complete_corpus"] and canonical(source) != canonical(PINNED_SOURCE))):
            raise StructuralError("pinned source completeness mismatch")
        p = meta["profile"]
        if p != policy(p["abbreviations"]) or meta["profile_sha256"] != digest(p):
            raise StructuralError("profile mismatch")
        if meta["implementation_sha256"] != _implementation():
            raise StructuralError("implementation mismatch; explicit migration required")
        raw_count = _verify_raw_source(db, meta["complete_corpus"])
        if canonical(_manifest(db)) != canonical(manifest):
            raise StructuralError("receipt or manifest mismatch")
        _verify_source(db, meta, raw_count)
        chars = dict(db.execute("SELECT id,scalar FROM characters"))
        words = dict(db.execute("SELECT id,surface FROM words"))
        word_ids = {word: wid for wid, word in words.items()}
        if list(chars.items()) != list(enumerate(sorted(chars.values(), key=ord), 1)) or list(words.items()) != list(enumerate(sorted(words.values()), 1)):
            raise StructuralError("identity ordering mismatch")
        if meta["complete_corpus"]:
            producer = meta["producer"]
            carrier = producer.get("carrier", [])
            if (set(producer) != {"repository", "commit", "module_sha256", "carrier_sha256", "carrier"}
                or producer.get("repository") != "The-Interdependency/ucns"
                or producer.get("carrier_sha256") != PUBLIC_GONOL_SHA256
                or producer.get("commit") != UCNS_PUBLIC_GONOL_COMMIT
                or producer.get("module_sha256") != UCNS_PUBLIC_GONOL_MODULE_SHA256
                or len(carrier) != 157 or len(set(carrier)) != 157
                or digest(carrier) != PUBLIC_GONOL_SHA256):
                raise StructuralError("carrier producer mismatch")
            positions = {c: i for i, c in enumerate(carrier)}
            if any(pos != positions.get(c) for c, pos in db.execute("SELECT scalar,public_position FROM characters")):
                raise StructuralError("carrier position mismatch")
        elif db.execute("SELECT COUNT(*) FROM characters WHERE public_position IS NOT NULL").fetchone()[0]:
            raise StructuralError("partial fields refuse unverified carrier positions")
        for wid, word in words.items():
            parts = segment(word, p["abbreviations"])
            glyphs = db.execute("SELECT ordinal,character_id FROM word_characters WHERE word_id=? ORDER BY ordinal", (wid,)).fetchall()
            if [n for n, c in glyphs] != list(range(len(word))):
                raise StructuralError("word occurrence ordinal mismatch")
            recovered = "".join(chars[c] for n, c in glyphs)
            if recovered != word or len(parts) != 1 or parts[0].kind != "word":
                raise StructuralError("word closure/recovery failure")
        for rid, kind, text, owner, origin, ordinal, previous, prov, state in db.execute("SELECT * FROM records ORDER BY id"):
            expected = segment(text, p["abbreviations"])
            rows = db.execute("SELECT ordinal,kind,word_id,character_id,start_offset,end_offset,function FROM components WHERE record_id=? ORDER BY ordinal", (rid,)).fetchall()
            if len(rows) != len(expected):
                raise StructuralError("participation count mismatch")
            for j, (row, part) in enumerate(zip(rows, expected, strict=True)):
                n, pk, wid, cid, start, end, function = row
                surface = words[wid] if pk == "word" else chars[cid]
                if (n, pk, surface, start, end, function) != (j, part.kind, part.text, part.start, part.end, _function(part)):
                    raise StructuralError("source participation mismatch")
            if kind == "definition":
                parent = db.execute("SELECT text,origin_word_id,kind FROM records WHERE id=?", (owner,)).fetchone()
                if parent is None or parent[2] != "lexical" or parent[1] != origin:
                    raise StructuralError("definition origin mismatch")
                earlier = db.execute("SELECT id FROM records WHERE kind='definition' AND owner_record_id=? AND ordinal=?", (owner, ordinal - 1)).fetchone()
                if previous != (earlier[0] if earlier else None) or (ordinal > 0 and earlier is None):
                    raise StructuralError("definition succession mismatch")
            else:
                expected_origin = word_ids.get(text)
                if owner is not None or previous is not None or origin != expected_origin:
                    raise StructuralError("lexical origin mismatch")
            if state != ("attached" if origin is not None else "hmmm:compound-lexical-origin"):
                raise StructuralError("origin status mismatch")
        yield db, manifest


def verify(out_dir: str | Path) -> dict:
    """Verify canonical rows and source spans, then close the read snapshot."""
    with _verified_connection(out_dir) as (_db, manifest):
        return manifest


def _verify_source(db: sqlite3.Connection, meta: dict, raw_count: int) -> None:
    """Reconcile the entire construction against preserved native source records."""
    evidence = {}
    for kind in ("lexeme", "synset"):
        rows = db.execute("SELECT ordinal,payload FROM evidence WHERE kind=? ORDER BY ordinal", (kind,)).fetchall()
        if [r[0] for r in rows] != list(range(len(rows))):
            raise StructuralError("source evidence order mismatch")
        evidence[kind] = []
        for _ordinal, payload in rows:
            item = json.loads(payload)
            if payload != _encoded(item):
                raise StructuralError("noncanonical source evidence payload")
            evidence[kind].append(item)
    evidence_sha256 = _evidence_digest(
        (kind, i, item) for kind in ("lexeme", "synset")
        for i, item in enumerate(evidence[kind]))
    if evidence_sha256 != meta["source"]["evidence_sha256"]:
        raise StructuralError("source evidence digest mismatch")
    if db.execute("SELECT COUNT(*) FROM evidence").fetchone()[0] != raw_count + sum(map(len, evidence.values())):
        raise StructuralError("unknown source evidence kind")
    if (len(evidence["lexeme"]), len(evidence["synset"])) != (meta["source"]["lexemes"], meta["source"]["synsets"]):
        raise StructuralError("source coverage mismatch")
    lexical = sorted({s for lex in evidence["lexeme"] for s in (lex["lemma"], *lex["forms"])} |
                     {s for syn in evidence["synset"] for s in syn["members"]})
    expected_abbreviations = sorted(set(DEFAULT_ABBREVIATIONS) |
                                   {s[:-1] for s in lexical if s.endswith(".") and s[:-1].isalpha()})
    if meta["profile"]["abbreviations"] != expected_abbreviations:
        raise StructuralError("abbreviation admission mismatch")
    words = dict(db.execute("SELECT surface,id FROM words"))
    texts = lexical + [text for syn in evidence["synset"] for text in syn["definitions"]]
    expected_words = {part.text for text in texts for part in segment(text, expected_abbreviations) if part.kind == "word"}
    if set(words) != expected_words:
        raise StructuralError("word admission coverage mismatch")
    if {r[0] for r in db.execute("SELECT scalar FROM characters")} != {c for text in texts for c in text}:
        raise StructuralError("glyph admission coverage mismatch")
    records = iter(db.execute("SELECT * FROM records ORDER BY id"))
    entries = {}
    rid = 0

    def check(kind, text, owner, origin, ordinal, previous, provenance):
        nonlocal rid
        rid += 1
        state = "attached" if origin is not None else "hmmm:compound-lexical-origin"
        expected = (rid, kind, text, owner, origin, ordinal, previous, _encoded(provenance), state)
        if next(records, None) != expected:
            raise StructuralError("source construction coverage/provenance mismatch")
        return rid

    for ordinal, text in enumerate(lexical):
        entries[text] = check("lexical", text, None, words.get(text), ordinal, None,
                              {"source": "corpus-lexical-membership"})
    synsets = {s["synset_id"]: s for s in evidence["synset"]}
    ordinals, previous = {}, {}
    for li, lexeme in enumerate(evidence["lexeme"]):
        lemma = lexeme["lemma"]
        for si, sense in enumerate(lexeme["senses"]):
            for di, text in enumerate(synsets[sense["synset_id"]]["definitions"]):
                ordinal = ordinals.get(lemma, 0)
                new_id = check("definition", text, entries[lemma], words.get(lemma), ordinal, previous.get(lemma),
                               {"lexeme_ordinal": li, "sense_ordinal": si, "definition_index": di,
                                "sense_id": sense["sense_id"], "synset_id": sense["synset_id"],
                                "part_of_speech": lexeme["part_of_speech"]})
                previous[lemma] = new_id
                ordinals[lemma] = ordinal + 1
    if next(records, None) is not None:
        raise StructuralError("unexpected source constructions")


def run(*, source_root: str | Path, ucns_source_root: str | Path, out_dir: str | Path) -> dict:
    """Production entrypoint: exact, clean corpus and carrier, entire source only."""
    source = Path(source_root).resolve()
    repo = source.parent.parent
    try:
        head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain", "--", "src/yaml"], text=True)
    except subprocess.CalledProcessError as exc:
        raise StructuralError("source repository unavailable") from exc
    if head != OEWN_COMMIT or dirty or source != repo / "src/yaml":
        raise StructuralError("corpus must be exact pinned clean source")
    carrier = _load_verified_public_gonol(ucns_source_root)
    snapshot = load_oewn_2025(source)
    return build(snapshot, out_dir=out_dir, public_position=carrier.public_gonol_position,
                 producer={"repository": "The-Interdependency/ucns", "commit": UCNS_PUBLIC_GONOL_COMMIT,
                           "module_sha256": UCNS_PUBLIC_GONOL_MODULE_SHA256,
                           "carrier_sha256": PUBLIC_GONOL_SHA256,
                           "carrier": list(carrier.PUBLIC_GONOL_157)}, complete_corpus=True, source_root=source)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    b = commands.add_parser("build")
    b.add_argument("--source-root", required=True)
    b.add_argument("--ucns-source-root", required=True)
    b.add_argument("--out-dir", required=True)
    v = commands.add_parser("verify")
    v.add_argument("out_dir")
    args = vars(parser.parse_args())
    command = args.pop("command")
    print(json.dumps(run(**args) if command == "build" else verify(**args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# ratios: loc_comments=540:80 imports_exports=19:6 calls_definitions=333:23
