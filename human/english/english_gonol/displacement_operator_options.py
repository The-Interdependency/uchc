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
