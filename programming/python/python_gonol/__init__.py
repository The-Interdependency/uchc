# ratios: loc_comments=30:27 imports_exports=1:1 calls_definitions=0:0
"""Public surface for stack-local Python Gonol Construction.

The builder consumes UCNS Unicode glyphs and optional Public Gonol positions, gives
every decoded scalar one shared identity, keeps every source occurrence
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
#   unresolved: Python grammar relations and runtime equivalence remain open
# === END MODULE_BUILD ===

from .construct import (
    PUBLIC_GONOL_SHA256,
    SCHEMA,
    UCNS_COMMIT,
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
    "UCNS_COMMIT",
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
# ratios: loc_comments=30:27 imports_exports=1:1 calls_definitions=0:0
