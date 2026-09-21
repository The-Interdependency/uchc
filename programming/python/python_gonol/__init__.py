"""Public surface for stack-local Python Gonol Construction.

The builder consumes UCNS's exact 157-position Public Gonol carrier, gives
every admitted glyph one shared identity, keeps every source occurrence
addressable in exact order, materializes one compact SQLite construct plus a
small manifest, and replays logically. Tokens and AST nodes verify the
construction; they never substitute for it.
"""

# === MODULE_BUILD ===
# id: python_gonol_public_surface
#   module_name: python_gonol
#   module_kind: facade
#   summary: exposes the compact SQLite shared-identity Python 3.12 source constructor and logical replay
#   owner: Python Gonol Construction (stack-local research)
#   public_surface: affixiate_python_source, affixiate_python_bytes, verify_construct, reconstruct_source, ConstructResult, PythonGonolConstructionError, SCHEMA, VERSION, UCNS_PUBLIC_GONOL_COMMIT, PUBLIC_GONOL_SHA256
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: caller-owned source only
#   admin_only: false
#   tests: tests.test_construct
#   rollout: explicit import only
#   rollback: remove package exports with the workspace
#   requires: python_gonol_construct
#   since: 2026-09-15
#   unresolved: deeper geometric functions and arbitrary Unicode admission remain hmmm
# === END MODULE_BUILD ===

from .construct import (
    PUBLIC_GONOL_SHA256,
    SCHEMA,
    UCNS_PUBLIC_GONOL_COMMIT,
    VERSION,
    ConstructResult,
    PythonGonolConstructionError,
    affixiate_python_bytes,
    affixiate_python_source,
    build_construct,
    load_verified_public_gonol,
    reconstruct_source,
    verify_construct,
)

__all__ = [
    "PUBLIC_GONOL_SHA256",
    "SCHEMA",
    "UCNS_PUBLIC_GONOL_COMMIT",
    "VERSION",
    "ConstructResult",
    "PythonGonolConstructionError",
    "affixiate_python_bytes",
    "affixiate_python_source",
    "build_construct",
    "load_verified_public_gonol",
    "reconstruct_source",
    "verify_construct",
]
