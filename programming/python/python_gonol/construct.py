# ratios: loc_comments=613:108 imports_exports=16:10 calls_definitions=165:20
# === MODULE_BUILD ===
# id: python_gonol_construct
#   module_name: python_gonol.construct
#   module_kind: engine
#   summary: exact Python 3.12 source construction with shared glyph identities, ordered occurrence references, compact SQLite materialization, and logical replay; consumes native UCNS Unicode glyphs and optional Public Gonol positions
#   owner: Python Gonol Construction (stack-local research)
#   public_surface: SCHEMA, VERSION, UCNS_PUBLIC_GONOL_COMMIT, PUBLIC_GONOL_SHA256, PythonGonolConstructionError, ConstructResult, build_construct, affixiate_python_source, affixiate_python_bytes, verify_construct, reconstruct_source
#   internal_surface: verified UCNS Unicode and Public Gonol loader, encoding detection, control construction, logical newline construction, canonical receipt
#   auth_boundary: UCNS owns geometry and Public Gonol positions; METAPAT owns affixiation semantics; Python Gonol Construction owns source admission and Python relation construction
#   storage_boundary: one caller-selected construct directory with construct.db and manifest.json
#   network_boundary: none
#   user_data_boundary: reads caller-owned source; writes only the explicit construct directory
#   admin_only: false
#   tests: tests.test_construct
#   rollout: explicit Python 3.12 stack-local candidate; not canon
#   rollback: delete the python-gonol workspace before downstream binding
#   requires: ucns_public_gonol_geometry (pinned checkout), Python 3.12 standard library
#   since: 2026-09-15
#   unresolved: Python grammar relations and runtime equivalence remain open
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: python_construct_preserves_source_bytes
#   given: admitted source bytes and their declared decoding
#   then: original bytes remain recoverable including a byte-order mark and replay binds them to the complete constructed source
#   class: provenance
#
# id: python_construct_physical_addresses
#   given: exact decoded source with LF, CR, and CRLF physical line endings
#   then: one-based scalar columns preserve both CRLF constituents and advance to the next physical line exactly once
#   class: construction
#
# id: python_construct_consumes_pinned_public_gonol_exactly
#   given: a UCNS checkout at the pinned commit
#   then: the exact 157-position Public Gonol carrier and its digest are consumed; the builder never copies, extends, or reinterprets the carrier
#   class: boundary
#
# id: python_construct_one_shared_identity_per_glyph
#   given: any admitted Python source
#   then: each decoded scalar has its native Unicode identity and every source occurrence references it in exact order with address, line, column, and provenance
#   class: construction
#
# id: python_construct_controls_are_constitutive
#   given: TAB, LF, FF, or CR occurrences
#   then: each closes a control construction whose Unicode name and code point are constitutive participants, never metadata, and TAB records exact spaces to the next eight-column stop
#   class: construction
#
# id: python_construct_newlines_remain_source_distinct
#   given: LF, CR, and CR+LF occurrences
#   then: each logical newline records its exact ordered source constituents and the three kinds remain distinct
#   class: construction
#
# id: python_construct_unicode_identity
#   given: any decoded Unicode scalar, including controls and supplementary-plane characters
#   then: its native glyph, UTF-32BE diameter, UTF-8 spelling and exact bearing are retained, with an optional Public Gonol position
#   class: safety
#
# id: python_construct_replay_fails_closed_on_tamper
#   given: a materialized construct
#   then: replay rebuilds source and controls from occurrences and fails closed on any identity, relation, order, or provenance drift
#   class: replay
#
# id: python_construct_tokens_verify_never_substitute
#   given: CPython tokenize and AST witnesses
#   then: their outcomes are recorded as verification only; no token, AST, code, or compiler object becomes a gonol
#   class: boundary
# === END CONTRACTS ===

"""Exact Python 3.12 source construction using the English method.

Every Unicode scalar has one native identity, including control characters. Each
source occurrence keeps its own address, order, multiplicity, relation, and
provenance, and references the shared identity. The materialized artifact is
one compact SQLite database plus a small manifest, never a giant JSON
receipt.

Control construction::

    CHARACTER TABULATION + U+0009 -> TAB
    LINE FEED          + U+000A -> LF
    FORM FEED          + U+000C -> FF
    CARRIAGE RETURN    + U+000D -> CR

Names and code points are constitutive participants. TAB affixiates with
enough SPACE gonols to reach the next eight-column stop. CR, LF, and CR+LF
construct logical newlines while preserving their exact source constituents.

CPython ``tokenize`` and ``ast`` verify the construction; they never
substitute for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import tokenize
from threading import Lock
from types import ModuleType
from typing import Any

SCHEMA = "python-gonol.full-construct"
VERSION = "3.0.0"

UCNS_COMMIT = "ee8addc0af36f02b64b42cb355734cb72a126ea5"
UCNS_PUBLIC_GONOL_COMMIT = UCNS_COMMIT
UCNS_PUBLIC_GONOL_MODULE_SHA256 = (
    "2da287ce9691b494fc921d14684a3bf7e0633f3a579ea040e3b6ddbaf0d92f27"
)
PUBLIC_GONOL_SHA256 = "55d10c84529a4d7bc7714786357e977b68d9df2ac3f73d20e229580b552c2ef5"

_NATIVE_SOURCES = {
    "public_gonol": UCNS_PUBLIC_GONOL_MODULE_SHA256,
    "scalar_bearing": "7d7ff1e1ddbd4997cdbee4f5f17a7c6fa4b8f3d55e288c97f700f610f32be7ac",
    "unicode_gonol": "5360325a51418835f6a4a3c037253ed79b35b2820073cf080ccda9d52cff0c5c",
}
_NATIVE_LOAD_LOCK = Lock()

_CONTROLS = {
    "\t": ("TAB", "CHARACTER TABULATION", "U+0009"),
    "\n": ("LF", "LINE FEED", "U+000A"),
    "\f": ("FF", "FORM FEED", "U+000C"),
    "\r": ("CR", "CARRIAGE RETURN", "U+000D"),
}

_HMMM = "Python grammar relations and runtime equivalence remain open."


class PythonGonolConstructionError(ValueError):
    """Raised when construction or replay fails closed."""


@dataclass(frozen=True)
class ConstructResult:
    schema: str
    version: str
    source_id: str
    encoding: str
    source_bytes_sha256: str
    decoded_source_sha256: str
    character_count: int
    occurrence_count: int
    control_count: int
    newline_count: int
    tokenize_ok: bool
    ast_ok: bool
    preflight_storage_bytes: int
    receipt_sha256: str


def _git(repo: Path, *arguments: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *arguments],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except (subprocess.CalledProcessError, OSError) as exc:
        raise PythonGonolConstructionError(f"UCNS checkout verification failed: {exc}") from exc


def producer_identity() -> dict:
    return {"commit": UCNS_COMMIT, "module_sha256": dict(_NATIVE_SOURCES),
            "public_gonol_sha256": PUBLIC_GONOL_SHA256, "scalar_encoding": "UTF-32BE"}


@lru_cache(maxsize=1)
def _load_modules(sources: tuple[tuple[str, bytes], ...]) -> ModuleType:
    # Only the already-verified bytes can supply relative imports in this namespace.
    package = ModuleType("_python_gonol_ucns_" + UCNS_COMMIT)
    package.__path__ = []
    sys.modules[package.__name__] = package
    try:
        for name, source in sources:
            module = ModuleType(f"{package.__name__}.{name}")
            module.__package__ = package.__name__
            module.__file__ = f"src/ucns/{name}.py"
            sys.modules[module.__name__] = module
            exec(compile(source, module.__file__, "exec"), module.__dict__)
            setattr(package, name, module)
    except BaseException:
        for name, _ in sources:
            sys.modules.pop(f"{package.__name__}.{name}", None)
        sys.modules.pop(package.__name__, None)
        raise
    return package


def _verified_geometry(ucns_source_root: str | Path) -> ModuleType:
    root = Path(ucns_source_root).resolve()
    _git(root, "merge-base", "--is-ancestor", UCNS_COMMIT, "HEAD")
    paths = {name: Path("src/ucns") / f"{name}.py" for name in _NATIVE_SOURCES}
    _git(root, "diff", "--quiet", "HEAD", "--", *(str(path) for path in paths.values()))
    sources = []
    for name, path in paths.items():
        try:
            source = (root / path).read_bytes()
        except OSError as exc:
            raise PythonGonolConstructionError(f"missing UCNS source: {path}") from exc
        if sha256(source).hexdigest() != _NATIVE_SOURCES[name]:
            raise PythonGonolConstructionError(f"UCNS module digest mismatch: {path}")
        sources.append((name, source))
    with _NATIVE_LOAD_LOCK:
        return _load_modules(tuple(sources))


def load_verified_public_gonol(ucns_source_root: str | Path) -> ModuleType:
    """Return the verified Public Gonol projection used by the constructor."""
    return _verified_geometry(ucns_source_root).public_gonol


_SCHEMA_SQL = """
PRAGMA foreign_keys=ON;
PRAGMA journal_mode=DELETE;
PRAGMA synchronous=FULL;

CREATE TABLE meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE source_bytes (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    data BLOB NOT NULL
);

CREATE TABLE characters (
    id INTEGER PRIMARY KEY,
    scalar TEXT NOT NULL UNIQUE,
    public_position INTEGER,
    utf32_be BLOB NOT NULL CHECK(length(utf32_be) = 4),
    utf8 BLOB NOT NULL,
    turn_numerator INTEGER NOT NULL,
    turn_denominator INTEGER NOT NULL,
    glyph_receipt TEXT NOT NULL
);

CREATE TABLE occurrences (
    id INTEGER PRIMARY KEY,
    ordinal INTEGER NOT NULL UNIQUE,
    scalar TEXT NOT NULL,
    character_id INTEGER NOT NULL REFERENCES characters(id),
    control_kind TEXT,
    address TEXT NOT NULL,
    start INTEGER NOT NULL,
    end INTEGER NOT NULL,
    line INTEGER NOT NULL,
    column INTEGER NOT NULL
);

CREATE TABLE control_identities (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL UNIQUE,
    name_text TEXT NOT NULL,
    code_point_text TEXT NOT NULL,
    member_ids TEXT NOT NULL
);

CREATE TABLE controls (
    id INTEGER PRIMARY KEY,
    occurrence_id INTEGER NOT NULL UNIQUE REFERENCES occurrences(id),
    control_identity_id INTEGER NOT NULL REFERENCES control_identities(id),
    start_column INTEGER NOT NULL,
    spaces_to_next_stop INTEGER NOT NULL,
    space_character_id INTEGER REFERENCES characters(id)
);

CREATE TABLE newlines (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,
    occurrence_ids TEXT NOT NULL
);
"""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _logical_sha256(connection: sqlite3.Connection) -> str:
    """Bind every constitutive row and metadata field except the self-receipt."""
    tables = ("characters", "occurrences", "control_identities", "controls", "newlines", "source_bytes", "meta")
    actual = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if actual != set(tables):
        raise PythonGonolConstructionError("construct table inventory mismatch")
    digest = sha256()
    schema = connection.execute("SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name").fetchall()
    digest.update(_canonical_bytes(schema))
    for table in tables:
        digest.update(_canonical_bytes(table))
        query = ("SELECT * FROM meta WHERE key != 'receipt_sha256' ORDER BY key"
                 if table == "meta" else f"SELECT * FROM {table} ORDER BY id")
        cursor = connection.execute(query)
        digest.update(_canonical_bytes([column[0] for column in cursor.description]))
        for row in cursor:
            digest.update(_canonical_bytes([{"bytes_hex": value.hex()} if isinstance(value, bytes) else value for value in row]))
            digest.update(b"\n")
    return digest.hexdigest()


def _detect_encoding(source_bytes: bytes) -> str:
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(source_bytes).readline)
    except (SyntaxError, UnicodeDecodeError) as exc:
        raise PythonGonolConstructionError(f"encoding declaration could not be detected: {exc}") from exc
    return encoding


def _address(source_id: str, ordinal: int) -> str:
    return f"{source_id}#character:{ordinal}"


def _source_positions(source: str):
    """Yield one-based physical addresses; CRLF retains both source scalars."""

    line = column = 1
    for index, scalar in enumerate(source):
        yield line, column
        if scalar == "\n" or (
            scalar == "\r" and source[index + 1:index + 2] != "\n"
        ):
            line += 1
            column = 1
        else:
            column += 1


def _control_identity_rows(
    character_id_by_scalar: dict[str, int],
) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for kind, name_text, code_point_text in _CONTROLS.values():
        member_ids: list[int] = []
        for scalar in name_text + code_point_text:
            if scalar not in character_id_by_scalar:
                raise PythonGonolConstructionError(
                    f"missing Unicode control participant: {scalar!r}"
                )
            member_ids.append(character_id_by_scalar[scalar])
        rows.append((kind, name_text, code_point_text, json.dumps(member_ids, separators=(",", ":"))))
    return rows


def _build_control_rows(
    source: str,
    occurrences: list[dict[str, Any]],
    character_id_by_scalar: dict[str, int],
    control_identity_id_by_kind: dict[str, int],
) -> tuple[list[tuple[int, int, int, int, int | None]], list[tuple[str, str]]]:
    control_rows: list[tuple[int, int, int, int, int | None]] = []
    newline_rows: list[tuple[str, str]] = []

    index = 0
    length = len(source)
    space_character_id = character_id_by_scalar.get(" ")
    expanded_column = 0

    while index < length:
        scalar = source[index]
        control = _CONTROLS.get(scalar)
        if control is None:
            expanded_column += 1
            index += 1
            continue
        kind, _name, _code_point = control
        occurrence = occurrences[index]
        column = occurrence["column"]

        if kind == "TAB":
            spaces = 8 - (expanded_column % 8)
            expanded_column += spaces
            control_rows.append(
                (
                    occurrence["id"],
                    control_identity_id_by_kind[kind],
                    column,
                    spaces,
                    space_character_id,
                )
            )
            index += 1
        elif kind == "CR":
            expanded_column = 0
            control_rows.append(
                (
                    occurrence["id"],
                    control_identity_id_by_kind[kind],
                    column,
                    0,
                    None,
                )
            )
            if index + 1 < length and source[index + 1] == "\n":
                cr_id = occurrence["id"]
                lf_id = occurrences[index + 1]["id"]
                lf_column = occurrences[index + 1]["column"]
                control_rows.append(
                    (
                        lf_id,
                        control_identity_id_by_kind["LF"],
                        lf_column,
                        0,
                        None,
                    )
                )
                newline_rows.append(("CRLF", json.dumps([cr_id, lf_id], separators=(",", ":"))))
                index += 2
            else:
                newline_rows.append(("CR", json.dumps([occurrence["id"]], separators=(",", ":"))))
                index += 1
        else:
            expanded_column = expanded_column + 1 if kind == "FF" else 0
            control_rows.append(
                (
                    occurrence["id"],
                    control_identity_id_by_kind[kind],
                    column,
                    0,
                    None,
                )
            )
            if kind != "FF":
                newline_rows.append((kind, json.dumps([occurrence["id"]], separators=(",", ":"))))
            index += 1

    return control_rows, newline_rows


def build_construct(
    source: str,
    *,
    source_bytes: bytes,
    source_id: str,
    encoding: str,
    state_dir: Path,
    ucns_source_root: str | Path,
    overwrite: bool = False,
) -> ConstructResult:
    """Build the compact SQLite construct and manifest."""

    try:
        if source_bytes.decode(encoding) != source:
            raise PythonGonolConstructionError("source bytes and decoded source disagree")
    except (UnicodeDecodeError, LookupError) as exc:
        raise PythonGonolConstructionError("source bytes do not match the declared encoding") from exc

    native = _verified_geometry(ucns_source_root)
    public_gonol = native.public_gonol
    carrier = public_gonol.PUBLIC_GONOL_157
    carrier_set = set(carrier)
    position_by_scalar = public_gonol.public_gonol_position

    if len(carrier) != 157 or len(carrier_set) != 157:
        raise PythonGonolConstructionError("pinned Public Gonol carrier is malformed")
    if public_gonol.public_gonol_sha256() != PUBLIC_GONOL_SHA256:
        raise PythonGonolConstructionError("pinned Public Gonol arrangement digest mismatch")

    try:
        decoded_source_sha256 = sha256(source.encode("utf-8")).hexdigest()
    except UnicodeEncodeError as exc:
        raise PythonGonolConstructionError("decoded source contains a surrogate") from exc

    state_dir.mkdir(parents=True, exist_ok=True)
    if overwrite:
        # Stage both files first. Interrupted publication is rejected by replay
        # and can be retried from the original source.
        with tempfile.TemporaryDirectory(prefix=".python-gonol-", dir=state_dir) as tmp:
            stage = Path(tmp)
            result = build_construct(source, source_bytes=source_bytes, source_id=source_id,
                                     encoding=encoding, state_dir=stage, ucns_source_root=ucns_source_root)
            (stage / "construct.db").replace(state_dir / "construct.db")
            (stage / "manifest.json").replace(state_dir / "manifest.json")
            return result
    db_path = state_dir / "construct.db"
    manifest_path = state_dir / "manifest.json"
    if db_path.exists() or manifest_path.exists():
        raise PythonGonolConstructionError(
            f"construct output already exists in {state_dir}; pass --overwrite"
        )

    source_bytes_sha256 = sha256(source_bytes).hexdigest()

    # Token/AST verification only; failures never block construction.
    tokenize_ok = True
    try:
        list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        tokenize_ok = False
    ast_ok = True
    try:
        import ast

        ast.parse(source, filename=source_id, mode="exec", feature_version=(3, 12))
    except (SyntaxError, ValueError):
        ast_ok = False

    occurrences: list[dict[str, Any]] = []
    characters = []
    character_id_by_scalar = {}
    for scalar in sorted(carrier_set.union(source)):
        glyph = native.unicode_gonol.unicode_glyph_gonol(scalar)
        character_id_by_scalar[scalar] = glyph.scalar
        characters.append((glyph.scalar, scalar, position_by_scalar(scalar), glyph.utf32_be,
                           glyph.utf8, glyph.turn.numerator, glyph.turn.denominator, glyph.receipt))

    for ordinal, (scalar, (line, column)) in enumerate(zip(source, _source_positions(source))):
        occurrences.append(
            {
                "id": ordinal + 1,
                "ordinal": ordinal,
                "scalar": scalar,
                "character_id": character_id_by_scalar[scalar],
                "control_kind": _CONTROLS.get(scalar, (None,))[0],
                "address": _address(source_id, ordinal),
                "start": ordinal,
                "end": ordinal + 1,
                "line": line,
                "column": column,
            }
        )

    control_identity_rows = _control_identity_rows(character_id_by_scalar)

    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(_SCHEMA_SQL)
        connection.execute("INSERT INTO source_bytes(id, data) VALUES(1, ?)", (source_bytes,))
        connection.executemany(
            "INSERT INTO characters(id, scalar, public_position, utf32_be, utf8, turn_numerator, turn_denominator, glyph_receipt) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            characters,
        )
        connection.executemany(
            "INSERT INTO occurrences(id, ordinal, scalar, character_id, control_kind, address, start, end, line, column) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    item["id"],
                    item["ordinal"],
                    item["scalar"],
                    item["character_id"],
                    item["control_kind"],
                    item["address"],
                    item["start"],
                    item["end"],
                    item["line"],
                    item["column"],
                )
                for item in occurrences
            ],
        )
        connection.executemany(
            "INSERT INTO control_identities(kind, name_text, code_point_text, member_ids) VALUES(?, ?, ?, ?)",
            control_identity_rows,
        )
        control_identity_id_by_kind = {
            row[1]: row[0] for row in connection.execute(
                "SELECT id, kind FROM control_identities"
            )
        }
        control_rows, newline_rows = _build_control_rows(
            source,
            occurrences,
            character_id_by_scalar,
            control_identity_id_by_kind,
        )
        connection.executemany(
            "INSERT INTO controls(occurrence_id, control_identity_id, start_column, spaces_to_next_stop, space_character_id) "
            "VALUES(?, ?, ?, ?, ?)",
            control_rows,
        )
        connection.executemany(
            "INSERT INTO newlines(kind, occurrence_ids) VALUES(?, ?)",
            newline_rows,
        )
        control_count = len(control_rows)
        newline_count = len(newline_rows)

        payload = {
            "schema": SCHEMA,
            "version": VERSION,
            "source_id": source_id,
            "encoding": encoding,
            "source_bytes_sha256": source_bytes_sha256,
            "decoded_source_sha256": decoded_source_sha256,
            "ucns": producer_identity(),
            "counts": {
                "characters": len(characters),
                "occurrences": len(occurrences),
                "controls": control_count,
                "newlines": newline_count,
            },
            "verification": {"tokenize_ok": tokenize_ok, "ast_ok": ast_ok},
            "preflight_storage_bytes": 65536 + len(source) * 256,
            "hmmm": _HMMM,
        }
        receipt_sha256 = sha256(_canonical_bytes(payload)).hexdigest()
        payload["receipt_sha256"] = receipt_sha256

        for key, value in (
            ("schema", SCHEMA),
            ("version", VERSION),
            ("source_id", source_id),
            ("encoding", encoding),
            ("source_bytes_sha256", source_bytes_sha256),
            ("decoded_source_sha256", decoded_source_sha256),
            ("public_gonol_sha256", PUBLIC_GONOL_SHA256),
            ("ucns_commit", UCNS_PUBLIC_GONOL_COMMIT),
            ("tokenize_ok", "true" if tokenize_ok else "false"),
            ("ast_ok", "true" if ast_ok else "false"),
            ("receipt_sha256", receipt_sha256),
        ):
            connection.execute("INSERT INTO meta(key, value) VALUES(?, ?)", (key, value))
        payload.pop("receipt_sha256")
        payload["construct_sha256"] = _logical_sha256(connection)
        receipt_sha256 = sha256(_canonical_bytes(payload)).hexdigest()
        payload["receipt_sha256"] = receipt_sha256
        connection.execute("UPDATE meta SET value=? WHERE key='receipt_sha256'", (receipt_sha256,))
        connection.commit()
    except Exception:
        connection.close()
        raise
    finally:
        connection.close()

    manifest_path.write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    return ConstructResult(
        schema=SCHEMA,
        version=VERSION,
        source_id=source_id,
        encoding=encoding,
        source_bytes_sha256=source_bytes_sha256,
        decoded_source_sha256=decoded_source_sha256,
        character_count=len(characters),
        occurrence_count=len(occurrences),
        control_count=control_count,
        newline_count=newline_count,
        tokenize_ok=tokenize_ok,
        ast_ok=ast_ok,
        preflight_storage_bytes=payload["preflight_storage_bytes"],
        receipt_sha256=receipt_sha256,
    )


def affixiate_python_source(
    source: str,
    *,
    source_id: str,
    ucns_source_root: str | Path,
    state_dir: Path,
    overwrite: bool = False,
) -> ConstructResult:
    """Construct an already-decoded Python 3.12 source string."""

    try:
        encoded = source.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise PythonGonolConstructionError("source contains a surrogate") from exc
    return build_construct(
        source,
        source_bytes=encoded,
        source_id=source_id,
        encoding="utf-8",
        state_dir=state_dir,
        ucns_source_root=ucns_source_root,
        overwrite=overwrite,
    )


def affixiate_python_bytes(
    source_bytes: bytes,
    *,
    source_id: str,
    ucns_source_root: str | Path,
    state_dir: Path,
    overwrite: bool = False,
) -> ConstructResult:
    """Detect encoding, preserve exact bytes, and construct the source."""

    encoding = _detect_encoding(source_bytes)
    try:
        source = source_bytes.decode(encoding)
    except (UnicodeDecodeError, LookupError) as exc:
        raise PythonGonolConstructionError(f"source bytes do not decode as declared: {exc}") from exc
    return build_construct(
        source,
        source_bytes=source_bytes,
        source_id=source_id,
        encoding=encoding,
        state_dir=state_dir,
        ucns_source_root=ucns_source_root,
        overwrite=overwrite,
    )


def reconstruct_source(state_dir: Path) -> str:
    """Reconstruct the exact decoded source from ordered occurrence references."""

    db_path = state_dir / "construct.db"
    if not db_path.is_file():
        raise PythonGonolConstructionError(f"construct database does not exist: {db_path}")
    connection = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA temp_store=MEMORY")
        rows = connection.execute(
            """
            SELECT o.scalar
            FROM occurrences AS o
            ORDER BY o.ordinal
            """
        ).fetchall()
    except sqlite3.Error as exc:
        raise PythonGonolConstructionError(f"construct database is not readable: {exc}") from exc
    finally:
        connection.close()
    return "".join(row[0] for row in rows)


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PythonGonolConstructionError("duplicate manifest key")
        result[key] = value
    return result


def verify_construct(
    state_dir: Path,
    ucns_source_root: str | Path,
) -> str:
    """Rebuild from preserved bytes in a temporary directory and compare all rows.

    The input construct stays read-only. Temporary replay output is removed on
    success or failure. Earlier schemas require rebuilding from original source bytes.
    """
    state_dir = Path(state_dir)
    db_path = state_dir / "construct.db"
    manifest_path = state_dir / "manifest.json"
    if not db_path.is_file() or not manifest_path.is_file():
        raise PythonGonolConstructionError("construct database or manifest is missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"), object_pairs_hook=_unique_json_object)
    except (OSError, json.JSONDecodeError) as exc:
        raise PythonGonolConstructionError("construct manifest is not readable JSON") from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA or manifest.get("version") != VERSION:
        raise PythonGonolConstructionError("construct manifest schema or version mismatch")
    connection = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA temp_store=MEMORY")
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise PythonGonolConstructionError("SQLite integrity failure")
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise PythonGonolConstructionError("construct foreign-key failure")
        observed = _logical_sha256(connection)
        if observed != manifest.get("construct_sha256"):
            raise PythonGonolConstructionError("construct content digest mismatch")
        source_rows = list(connection.execute("SELECT data FROM source_bytes ORDER BY id"))
        if len(source_rows) != 1 or not isinstance(source_rows[0][0], bytes):
            raise PythonGonolConstructionError("source byte inventory mismatch")
        raw = source_rows[0][0]
        recorded_receipt = connection.execute("SELECT value FROM meta WHERE key='receipt_sha256'").fetchone()
        if recorded_receipt != (manifest.get("receipt_sha256"),):
            raise PythonGonolConstructionError("stored receipt digest mismatch")
    except sqlite3.Error as exc:
        raise PythonGonolConstructionError(f"construct database is not readable: {exc}") from exc
    finally:
        connection.close()
    try:
        encoding = manifest["encoding"]
        source_id = manifest["source_id"]
        if not isinstance(encoding, str) or not isinstance(source_id, str):
            raise PythonGonolConstructionError("source provenance types are invalid")
        source = raw.decode(encoding)
    except (KeyError, UnicodeDecodeError, LookupError) as exc:
        raise PythonGonolConstructionError("source encoding/provenance mismatch") from exc
    with tempfile.TemporaryDirectory(prefix="python-gonol-replay-") as temporary:
        replay_dir = Path(temporary)
        build_construct(source, source_bytes=raw, source_id=source_id, encoding=encoding,
                        state_dir=replay_dir, ucns_source_root=ucns_source_root)
        expected = json.loads((replay_dir / "manifest.json").read_text(encoding="utf-8"))
    if expected != manifest:
        raise PythonGonolConstructionError("independent reconstruction differs from construct or manifest")
    return manifest["receipt_sha256"]


__all__ = [
    "SCHEMA",
    "VERSION",
    "UCNS_COMMIT",
    "UCNS_PUBLIC_GONOL_COMMIT",
    "PUBLIC_GONOL_SHA256",
    "PythonGonolConstructionError",
    "ConstructResult",
    "build_construct",
    "affixiate_python_source",
    "affixiate_python_bytes",
    "verify_construct",
    "reconstruct_source",
    "load_verified_public_gonol",
]
# ratios: loc_comments=613:108 imports_exports=16:10 calls_definitions=165:20
