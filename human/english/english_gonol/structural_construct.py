# ratios: loc_comments=313:45 imports_exports=15:6 calls_definitions=184:13
"""Complete English structural construction and byte-stable replay.

Usage: python -m english_gonol.structural_construct build --source-root PATH
--ucns-source-root PATH --out-dir NEW_PATH; use ``verify NEW_PATH`` to replay.
The source/profile/producer identity is part of the graph, not a renderer flag.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sqlite3
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
#   then: reconstruct every source text and verify graph bytes, source evidence, policy, counts and receipt
# === END CONTRACTS ===

SCHEMA = "english-gonol.structural-construct"
VERSION = "1.0.0"
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
    paths = ("structural_rules.py", "structural_construct.py", "structural_query.py",
             "hyperspace_construct.py", "full_construct_run.py", "language/source.py")
    return digest({name: sha256((root / name).read_bytes()).hexdigest() for name in paths})


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


def build(snapshot: WordnetSnapshot, *, out_dir: str | Path,
          public_position: Callable[[str], int | None], producer: dict,
          complete_corpus: bool = False) -> dict:
    """Build all supplied source records. Production ``run`` verifies full pins.

    Fixture builds are explicitly marked incomplete; callbacks supply carrier
    observations only and cannot confer UCNS authority or corpus completeness.
    """
    output = Path(out_dir).resolve()
    if output.exists():
        raise StructuralError("output already exists; use a new directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".structural-", dir=output.parent))
    db = sqlite3.connect(stage / "construct.db")
    try:
        db.executescript(SQL)
        lexical = sorted({s for lex in snapshot.lexemes for s in (lex.lemma, *lex.forms)} |
                         {s for syn in snapshot.synsets for s in syn.members})
        abbreviations = sorted(set(DEFAULT_ABBREVIATIONS) |
                               {s[:-1] for s in lexical if s.endswith(".") and s[:-1].isalpha()})
        admission_policy = policy(abbreviations)
        meta = {"profile": admission_policy, "profile_sha256": digest(admission_policy),
                "source": {"repository": OEWN_REPOSITORY, "commit": OEWN_COMMIT,
                           "tree_sha256": snapshot.source_tree_sha256,
                           "files": snapshot.source_file_count,
                           "lexemes": len(snapshot.lexemes), "synsets": len(snapshot.synsets)},
                "complete_corpus": complete_corpus, "producer": producer,
                "implementation_sha256": _implementation(),
                "geometry_state": "hmmm", "normalization": "none",
                "definition_topologies": ["constituent-chain", "constituent-direct", "definition-succession"],
                "authority_transfer": False}
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


def open_readonly(path: str | Path) -> sqlite3.Connection:
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)


def verify(out_dir: str | Path) -> dict:
    """Verify complete canonical rows and independently recover all source spans."""
    root = Path(out_dir)
    manifest = json.loads((root / "manifest.json").read_bytes())
    if (manifest.get("schema"), manifest.get("version")) != (SCHEMA, VERSION):
        raise StructuralError("schema/version mismatch")
    with closing(open_readonly(root / "construct.db")) as db:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables != set(TABLES):
            raise StructuralError("table set mismatch")
        if db.execute("PRAGMA integrity_check").fetchone() != ("ok",) or db.execute("PRAGMA foreign_key_check").fetchone():
            raise StructuralError("database integrity failure")
        if _manifest(db) != manifest:
            raise StructuralError("receipt or manifest mismatch")
        meta = manifest["metadata"]
        p = meta["profile"]
        if p != policy(p["abbreviations"]) or meta["profile_sha256"] != digest(p):
            raise StructuralError("profile mismatch")
        if meta["implementation_sha256"] != _implementation():
            raise StructuralError("implementation mismatch; explicit migration required")
        _verify_source(db, meta)
        chars = dict(db.execute("SELECT id,scalar FROM characters"))
        words = dict(db.execute("SELECT id,surface FROM words"))
        word_ids = {word: wid for wid, word in words.items()}
        if list(chars.items()) != list(enumerate(sorted(chars.values(), key=ord), 1)) or list(words.items()) != list(enumerate(sorted(words.values()), 1)):
            raise StructuralError("identity ordering mismatch")
        if meta["complete_corpus"]:
            producer = meta["producer"]
            carrier = producer.get("carrier", [])
            if (producer.get("commit") != UCNS_PUBLIC_GONOL_COMMIT
                or producer.get("module_sha256") != UCNS_PUBLIC_GONOL_MODULE_SHA256
                or len(carrier) != 157 or len(set(carrier)) != 157
                or digest(carrier) != PUBLIC_GONOL_SHA256):
                raise StructuralError("carrier producer mismatch")
            positions = {c: i for i, c in enumerate(carrier)}
            if any(pos != positions.get(c) for c, pos in db.execute("SELECT scalar,public_position FROM characters")):
                raise StructuralError("carrier position mismatch")
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
    return manifest


def _verify_source(db: sqlite3.Connection, meta: dict) -> None:
    """Reconcile the entire construction against preserved native source records."""
    evidence = {}
    for kind in ("lexeme", "synset"):
        rows = db.execute("SELECT ordinal,payload FROM evidence WHERE kind=? ORDER BY ordinal", (kind,)).fetchall()
        if [r[0] for r in rows] != list(range(len(rows))):
            raise StructuralError("source evidence order mismatch")
        evidence[kind] = [json.loads(r[1]) for r in rows]
    if db.execute("SELECT COUNT(*) FROM evidence").fetchone()[0] != sum(map(len, evidence.values())):
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
                           "carrier": list(carrier.PUBLIC_GONOL_157)}, complete_corpus=True)


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
# ratios: loc_comments=313:45 imports_exports=15:6 calls_definitions=184:13
