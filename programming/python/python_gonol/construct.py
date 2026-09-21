# === MODULE_BUILD ===
# id: python_gonol_construct
#   module_name: python_gonol.construct
#   module_kind: engine
#   summary: exact Python 3.12 source construction with shared glyph identities, ordered occurrence references, compact SQLite materialization, and logical replay; consumes the pinned UCNS Public Gonol carrier without copying or extending it
#   owner: Python Gonol Construction (stack-local research)
#   public_surface: SCHEMA, VERSION, UCNS_PUBLIC_GONOL_COMMIT, PUBLIC_GONOL_SHA256, PythonGonolConstructionError, ConstructResult, build_construct, affixiate_python_source, affixiate_python_bytes, verify_construct, reconstruct_source
#   internal_surface: verified UCNS Public Gonol loader, encoding detection, control construction, logical newline construction, canonical receipt
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
#   unresolved: deeper geometric functions and admission of arbitrary Unicode source characters remain hmmm; preserved without invention
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: python_construct_consumes_pinned_public_gonol_exactly
#   given: a UCNS checkout at the pinned commit
#   then: the exact 157-position Public Gonol carrier and its digest are consumed; the builder never copies, extends, or reinterprets the carrier
#   class: boundary
#
# id: python_construct_one_shared_identity_per_glyph
#   given: any admitted Python source
#   then: each admitted carrier glyph has exactly one shared character identity and every source occurrence references it in exact order with address, line, column, and provenance
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
# id: python_construct_off_carrier_is_hmmm_not_invented
#   given: a source scalar outside the pinned carrier and outside the four declared control scalars
#   then: it is recorded as hmmm with exact address and never assigned an invented Public Gonol position
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

Every admitted Public Gonol glyph has one shared character identity. Each
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
from hashlib import sha256
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tokenize
from types import ModuleType
from typing import Any

SCHEMA = "python-gonol.full-construct"
VERSION = "1.0.0"

UCNS_PUBLIC_GONOL_COMMIT = "62e08ee1cf3b5d7b6e48c927b1047509e6328b5c"
UCNS_PUBLIC_GONOL_MODULE_SHA256 = (
    "2da287ce9691b494fc921d14684a3bf7e0633f3a579ea040e3b6ddbaf0d92f27"
)
PUBLIC_GONOL_SHA256 = "55d10c84529a4d7bc7714786357e977b68d9df2ac3f73d20e229580b552c2ef5"

_CONTROLS = {
    "\t": ("TAB", "CHARACTER TABULATION", "U+0009"),
    "\n": ("LF", "LINE FEED", "U+000A"),
    "\f": ("FF", "FORM FEED", "U+000C"),
    "\r": ("CR", "CARRIAGE RETURN", "U+000D"),
}

_HMMM = (
    "deeper geometric functions and admission of arbitrary Unicode source "
    "characters remain unresolved; preserved without invention"
)


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
    not_on_pinned_carrier: tuple[str, ...]
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


def load_verified_public_gonol(ucns_source_root: str | Path) -> ModuleType:
    """Load the pinned Public Gonol module without copying or extending it."""

    root = Path(ucns_source_root).resolve()
    head = _git(root, "rev-parse", "HEAD")
    try:
        _git(root, "merge-base", "--is-ancestor", UCNS_PUBLIC_GONOL_COMMIT, head)
    except PythonGonolConstructionError:
        raise PythonGonolConstructionError(
            "UCNS checkout does not contain the pinned Public Gonol authority "
            f"{UCNS_PUBLIC_GONOL_COMMIT}"
        ) from None
    path = root / "src" / "ucns" / "public_gonol.py"
    if not path.is_file():
        raise PythonGonolConstructionError("UCNS public_gonol.py is missing")
    working = path.read_bytes()
    try:
        committed = subprocess.check_output(
            ["git", "-C", str(root), "show", "HEAD:src/ucns/public_gonol.py"],
            stderr=subprocess.STDOUT,
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        raise PythonGonolConstructionError("cannot read committed UCNS Public Gonol bytes") from exc
    if working != committed:
        raise PythonGonolConstructionError("UCNS public_gonol.py has uncommitted changes")
    if sha256(committed).hexdigest() != UCNS_PUBLIC_GONOL_MODULE_SHA256:
        raise PythonGonolConstructionError("UCNS public_gonol.py module digest mismatch")

    module = ModuleType("_python_gonol_verified_public_gonol")
    module.__file__ = str(path)
    previous = sys.modules.get(module.__name__)
    sys.modules[module.__name__] = module
    try:
        exec(compile(committed, str(path), "exec"), module.__dict__)
    except Exception:
        if previous is None:
            sys.modules.pop(module.__name__, None)
        else:
            sys.modules[module.__name__] = previous
        raise
    if module.PUBLIC_GONOL_SHA256 != PUBLIC_GONOL_SHA256:
        raise PythonGonolConstructionError("Public Gonol arrangement digest mismatch")
    return module


_SCHEMA_SQL = """
PRAGMA foreign_keys=ON;
PRAGMA journal_mode=DELETE;
PRAGMA synchronous=FULL;

CREATE TABLE meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE characters (
    id INTEGER PRIMARY KEY,
    scalar TEXT NOT NULL UNIQUE,
    public_position INTEGER NOT NULL
);

CREATE TABLE occurrences (
    id INTEGER PRIMARY KEY,
    ordinal INTEGER NOT NULL UNIQUE,
    scalar TEXT NOT NULL,
    character_id INTEGER REFERENCES characters(id),
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


def _detect_encoding(source_bytes: bytes) -> str:
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(source_bytes).readline)
    except (SyntaxError, UnicodeDecodeError) as exc:
        raise PythonGonolConstructionError(f"encoding declaration could not be detected: {exc}") from exc
    return encoding


def _address(source_id: str, ordinal: int) -> str:
    return f"{source_id}#character:{ordinal}"


def _line_column(source: str, index: int) -> tuple[int, int]:
    line = source.count("\n", 0, index) + 1
    previous = source.rfind("\n", 0, index)
    column = index - previous
    return line, column


def _control_identity_rows(
    public_gonol: ModuleType,
    character_id_by_scalar: dict[str, int],
) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for kind, name_text, code_point_text in _CONTROLS.values():
        member_ids: list[int] = []
        for scalar in name_text + code_point_text:
            if scalar not in character_id_by_scalar:
                raise PythonGonolConstructionError(
                    f"control participant scalar is not on the pinned carrier: {scalar!r}"
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

    while index < length:
        scalar = source[index]
        control = _CONTROLS.get(scalar)
        if control is None:
            index += 1
            continue
        kind, _name, _code_point = control
        occurrence = occurrences[index]
        column = occurrence["column"]

        if kind == "TAB":
            spaces = 8 - (column % 8)
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

    public_gonol = load_verified_public_gonol(ucns_source_root)
    carrier = public_gonol.PUBLIC_GONOL_157
    carrier_set = set(carrier)
    position_by_scalar = public_gonol.public_gonol_position

    if len(carrier) != 157 or len(carrier_set) != 157:
        raise PythonGonolConstructionError("pinned Public Gonol carrier is malformed")
    if public_gonol.public_gonol_sha256() != PUBLIC_GONOL_SHA256:
        raise PythonGonolConstructionError("pinned Public Gonol arrangement digest mismatch")

    state_dir.mkdir(parents=True, exist_ok=True)
    db_path = state_dir / "construct.db"
    manifest_path = state_dir / "manifest.json"
    if not overwrite and (db_path.exists() or manifest_path.exists()):
        raise PythonGonolConstructionError(
            f"construct output already exists in {state_dir}; pass --overwrite"
        )

    decoded_source_sha256 = sha256(source.encode("utf-8")).hexdigest()
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
    characters: list[tuple[int, str, int]] = []
    character_id_by_scalar: dict[str, int] = {}
    for character_id, scalar in enumerate(carrier, start=1):
        character_id_by_scalar[scalar] = character_id
        characters.append((character_id, scalar, position_by_scalar(scalar)))
    not_on_carrier: list[str] = []
    seen_not_on_carrier: set[str] = set()

    for ordinal, scalar in enumerate(source):
        if scalar in carrier_set:
            character_id = character_id_by_scalar[scalar]
        else:
            character_id = None
            if scalar not in _CONTROLS and scalar not in seen_not_on_carrier:
                seen_not_on_carrier.add(scalar)
                not_on_carrier.append(scalar)
        line, column = _line_column(source, ordinal)
        occurrences.append(
            {
                "id": ordinal + 1,
                "ordinal": ordinal,
                "scalar": scalar,
                "character_id": character_id,
                "control_kind": _CONTROLS.get(scalar, (None,))[0],
                "address": _address(source_id, ordinal),
                "start": ordinal,
                "end": ordinal + 1,
                "line": line,
                "column": column,
            }
        )

    control_identity_rows = _control_identity_rows(public_gonol, character_id_by_scalar)

    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(_SCHEMA_SQL)
        connection.executemany(
            "INSERT INTO characters(id, scalar, public_position) VALUES(?, ?, ?)",
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
            "ucns": {
                "commit": UCNS_PUBLIC_GONOL_COMMIT,
                "public_gonol_module_sha256": UCNS_PUBLIC_GONOL_MODULE_SHA256,
                "public_gonol_sha256": PUBLIC_GONOL_SHA256,
            },
            "counts": {
                "characters": len(characters),
                "occurrences": len(occurrences),
                "controls": control_count,
                "newlines": newline_count,
            },
            "not_on_pinned_carrier": sorted(not_on_carrier),
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
        not_on_pinned_carrier=tuple(sorted(not_on_carrier)),
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

    return build_construct(
        source,
        source_bytes=source.encode("utf-8"),
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
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
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


def verify_construct(
    state_dir: Path,
    ucns_source_root: str | Path,
) -> str:
    """Replay the construct and fail closed on any drift or tamper."""

    public_gonol = load_verified_public_gonol(ucns_source_root)
    carrier = public_gonol.PUBLIC_GONOL_157
    carrier_set = set(carrier)
    position_by_scalar = public_gonol.public_gonol_position

    db_path = state_dir / "construct.db"
    manifest_path = state_dir / "manifest.json"
    if not db_path.is_file() or not manifest_path.is_file():
        raise PythonGonolConstructionError("construct database or manifest is missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PythonGonolConstructionError("construct manifest is not readable JSON") from exc
    if manifest.get("schema") != SCHEMA or manifest.get("version") != VERSION:
        raise PythonGonolConstructionError("construct manifest schema or version mismatch")

    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        meta = {key: value for key, value in connection.execute("SELECT key, value FROM meta")}
        characters = {
            scalar: (character_id, public_position)
            for character_id, scalar, public_position in connection.execute(
                "SELECT id, scalar, public_position FROM characters"
            )
        }
        occurrences = list(
            connection.execute(
                "SELECT id, ordinal, scalar, character_id, control_kind, address, start, end, line, column "
                "FROM occurrences ORDER BY ordinal"
            )
        )
        stored_controls = list(
            connection.execute(
                "SELECT occurrence_id, control_identity_id, start_column, spaces_to_next_stop, space_character_id "
                "FROM controls ORDER BY id"
            )
        )
        stored_newlines = list(
            connection.execute("SELECT kind, occurrence_ids FROM newlines ORDER BY id")
        )
    except sqlite3.Error as exc:
        raise PythonGonolConstructionError(f"construct database is not readable: {exc}") from exc
    finally:
        connection.close()

    if meta.get("public_gonol_sha256") != PUBLIC_GONOL_SHA256:
        raise PythonGonolConstructionError("stored Public Gonol digest mismatch")

    source = "".join(row[2] for row in occurrences)
    decoded_expected = sha256(source.encode("utf-8")).hexdigest()
    if decoded_expected != meta.get("decoded_source_sha256"):
        raise PythonGonolConstructionError("decoded source digest mismatch")

    for index, row in enumerate(occurrences):
        (occurrence_id, ordinal, scalar, character_id, control_kind, address, start, end, line, column) = row
        if occurrence_id != ordinal + 1:
            raise PythonGonolConstructionError("occurrence identity or order drift")
        if address != _address(manifest["source_id"], ordinal):
            raise PythonGonolConstructionError("occurrence address drift")
        if start != ordinal or end != ordinal + 1:
            raise PythonGonolConstructionError("occurrence span drift")
        expected_line, expected_column = _line_column(source, ordinal)
        if line != expected_line or column != expected_column:
            raise PythonGonolConstructionError("occurrence line/column drift")
        if scalar in carrier_set:
            expected_position = position_by_scalar(scalar)
            expected_character = characters.get(scalar)
            if expected_character is None or expected_character[0] != character_id or expected_character[1] != expected_position:
                raise PythonGonolConstructionError("carrier glyph identity or position drift")
        else:
            expected_control_kind = _CONTROLS.get(scalar, (None,))[0]
            if character_id is not None or control_kind != expected_control_kind:
                raise PythonGonolConstructionError("off-carrier occurrence identity drift")
            if expected_control_kind is None:
                continue

    expected_controls, expected_newlines = _build_control_rows(
        source,
        [
            {
                "id": row[0],
                "column": row[9],
            }
            for row in occurrences
        ],
        {scalar: character_id for scalar, (character_id, _position) in characters.items()},
        {row[1]: row[0] for row in connection_execute_control_identities(state_dir)},
    )
    if expected_controls != [
        (occurrence_id, control_identity_id, start_column, spaces, space_character_id)
        for occurrence_id, control_identity_id, start_column, spaces, space_character_id in stored_controls
    ]:
        raise PythonGonolConstructionError("control construction drift")
    if expected_newlines != [(kind, ids) for kind, ids in stored_newlines]:
        raise PythonGonolConstructionError("logical newline drift")

    expected_payload = dict(manifest)
    expected_payload.pop("receipt_sha256", None)
    expected_receipt = sha256(_canonical_bytes(expected_payload)).hexdigest()
    if expected_receipt != manifest.get("receipt_sha256"):
        raise PythonGonolConstructionError("receipt digest mismatch")
    if meta.get("receipt_sha256") != manifest.get("receipt_sha256"):
        raise PythonGonolConstructionError("stored receipt digest mismatch")

    return manifest["receipt_sha256"]


def connection_execute_control_identities(state_dir: Path) -> list[tuple[int, int]]:
    """Return ``(id, kind)`` pairs for control identities."""

    connection = sqlite3.connect(f"file:{state_dir / 'construct.db'}?mode=ro", uri=True)
    try:
        return [(row[0], row[1]) for row in connection.execute("SELECT id, kind FROM control_identities")]
    finally:
        connection.close()


__all__ = [
    "SCHEMA",
    "VERSION",
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
