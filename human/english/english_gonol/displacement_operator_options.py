# === MODULE_BUILD ===
# id: english_gonol_displacement_operator_options
#   module_name: displacement_operator_options
#   module_kind: adjudication
#   summary: Read the two corpus-derived channel options for a word.
#   owner: Erin Spencer
#   public_surface: channel_option_a, channel_option_c
#   internal_surface: dictionary source order and constituent density
#   auth_boundary: none
#   storage_boundary: aggregate receipts only; per-word options recomputed on demand
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_displacement_operator_options
#   rollout: verified English dictionary consumer
#   rollback: remove this module, facade exports, tests, and candidate documentation
#   requires: english_gonol_hyperspace_views
#   since: 2026-09-27
#   unresolved: contextual sense selection
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: channel_options_are_built
#   given: a word identity
#   then: read its dictionary target and measured constituent overlap
#   class: correctness
# === END CONTRACTS ===
"""Read the two corpus-derived channel options for a word."""

import sqlite3

from .hyperspace_views import _definition_density


def channel_option_a(db: sqlite3.Connection, word_id: int) -> tuple[int, int, int]:
    """Return the word identity, its first semantic target and definition count."""

    count, first_target = db.execute(
        "SELECT COUNT(*), (SELECT e.target_word_id FROM semantic_evidence e "
        "WHERE e.definition_id = (SELECT id FROM definitions WHERE origin_word_id = ? "
        "ORDER BY ordinal LIMIT 1) ORDER BY e.id LIMIT 1) "
        "FROM definitions WHERE origin_word_id = ?", (word_id, word_id)
    ).fetchone()
    return word_id, first_target or 0, count


def channel_option_c(db: sqlite3.Connection, word_id: int) -> tuple[int, int, int]:
    """Option c: word id, definition inner-product shared sum, definition count."""

    density = _definition_density(db, word_id)
    shared = density["shared_sum"] if density else 0
    count = density["definition_count"] if density else 0
    return word_id, shared, count
