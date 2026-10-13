# === MODULE_BUILD ===
# id: uchc_polyglot_label_attachment
#   module_name: uchc_polyglot
#   module_kind: relation
#   summary: attaches language- and register-scoped surfaces to one UCNS geometric identity without making labels identity-bearing or asserting word-to-word translation
#   owner: Erin Spencer
#   public_surface: LabelAttachment, PolyglotReferent, PolyglotError, build_label_attachment, attach_label, same_referent
#   internal_surface: deterministic attachment digest, supersession-chain validation, current-label projection
#   auth_boundary: UCNS geometric identity is consumed by exact digest and schema/version only; UCHC does not recompute UCNS geometry
#   storage_boundary: immutable records only
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: shared/polyglot/tests/test_polyglot.py
#   rollout: candidate shared UCHC polyglot layer
#   rollback: remove package, tests, docs, and packaging entry
#   requires: ucns_axis_circle_position_candidate
#   since: 2026-10-05
#   unresolved: language-specific admission/construction profiles and semantic partitioning remain owned by each language implementation
# === END MODULE_BUILD ===
#
# === CONTRACTS ===
# id: polyglot_referent_identity_is_ucns_identity
#   given: any UCHC polyglot referent
#   then: its referent identity is exactly the consumed UCNS identity digest and is unchanged by label additions or supersession
#   class: correctness
#   since: 2026-10-05
#
# id: polyglot_labels_are_scoped_attachments
#   given: one UCNS identity
#   then: multiple language/register surfaces may attach independently with provenance and history
#   class: correctness
#   since: 2026-10-05
#
# id: polyglot_does_not_assert_pairwise_translation_identity
#   given: two labels on one referent
#   then: UCHC records that both attach to the same UCNS identity; it does not encode label A equals label B
#   class: doctrine
#   since: 2026-10-05
#
# id: polyglot_supersession_preserves_history
#   given: a later attachment supersedes an earlier attachment
#   then: both records remain addressable while current-label projection excludes the superseded attachment
#   class: correctness
#   since: 2026-10-05
#
# id: polyglot_fails_closed
#   given: malformed UCNS identity, duplicate attachment identity, dangling supersession, or malformed label
#   then: construction raises PolyglotError
#   class: safety
#   since: 2026-10-05
# === END CONTRACTS ===

"""Language labels attached to stable UCNS geometric identity.

This package owns no geometry. It consumes one exact UCNS identity digest and
allows language/register surfaces to attach to that referent.

A rename is a new attachment that may supersede an older one. The underlying
UCNS identity never changes. Multiple languages may attach concurrently.

No pairwise translation equality is created: two labels are related only by
their independent attachment to the same geometric referent.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Iterable

UCNS_SCHEMA = "ucns.axis-circle-position-candidate"
UCNS_VERSION = "0.1.0"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class PolyglotError(ValueError):
    """Raised when a polyglot attachment record fails closed."""


def _canonical(payload: dict[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _require_metadata_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PolyglotError(f"{name} must contain non-whitespace text")
    return value


def _require_surface(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise PolyglotError("surface must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class LabelAttachment:
    """One provenance-bearing surface attached to a UCNS referent."""

    ucns_identity_sha256: str
    language_tag: str
    surface: str
    scope: str
    source_id: str
    supersedes: str | None
    attachment_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.ucns_identity_sha256, str) or not _SHA256_RE.fullmatch(
            self.ucns_identity_sha256
        ):
            raise PolyglotError("ucns_identity_sha256 must be a lowercase hexadecimal SHA-256")
        for name in ("language_tag", "scope", "source_id"):
            _require_metadata_text(name, getattr(self, name))
        _require_surface(self.surface)
        if self.supersedes is not None and (
            not isinstance(self.supersedes, str)
            or not _SHA256_RE.fullmatch(self.supersedes)
        ):
            raise PolyglotError("supersedes must be a lowercase hexadecimal SHA-256 or None")
        expected = _attachment_digest(
            ucns_identity_sha256=self.ucns_identity_sha256,
            language_tag=self.language_tag,
            surface=self.surface,
            scope=self.scope,
            source_id=self.source_id,
            supersedes=self.supersedes,
        )
        if self.attachment_sha256 != expected:
            raise PolyglotError("attachment_sha256 does not match attachment content")

    def as_dict(self) -> dict[str, object]:
        return {
            "ucns_identity_sha256": self.ucns_identity_sha256,
            "language_tag": self.language_tag,
            "surface": self.surface,
            "scope": self.scope,
            "source_id": self.source_id,
            "supersedes": self.supersedes,
            "attachment_sha256": self.attachment_sha256,
        }


def _attachment_digest(
    *,
    ucns_identity_sha256: str,
    language_tag: str,
    surface: str,
    scope: str,
    source_id: str,
    supersedes: str | None,
) -> str:
    payload = {
        "ucns_schema": UCNS_SCHEMA,
        "ucns_version": UCNS_VERSION,
        "ucns_identity_sha256": ucns_identity_sha256,
        "language_tag": language_tag,
        "surface": surface,
        "scope": scope,
        "source_id": source_id,
        "supersedes": supersedes,
    }
    return sha256(_canonical(payload)).hexdigest()


def build_label_attachment(
    *,
    ucns_identity_sha256: str,
    language_tag: str,
    surface: str,
    scope: str,
    source_id: str,
    supersedes: str | None = None,
) -> LabelAttachment:
    """Build one immutable label attachment."""

    if not isinstance(ucns_identity_sha256, str) or not _SHA256_RE.fullmatch(
        ucns_identity_sha256
    ):
        raise PolyglotError("ucns_identity_sha256 must be a lowercase hexadecimal SHA-256")
    language_tag = _require_metadata_text("language_tag", language_tag)
    surface = _require_surface(surface)
    scope = _require_metadata_text("scope", scope)
    source_id = _require_metadata_text("source_id", source_id)
    if supersedes is not None and (
        not isinstance(supersedes, str) or not _SHA256_RE.fullmatch(supersedes)
    ):
        raise PolyglotError("supersedes must be a lowercase hexadecimal SHA-256 or None")
    return LabelAttachment(
        ucns_identity_sha256=ucns_identity_sha256,
        language_tag=language_tag,
        surface=surface,
        scope=scope,
        source_id=source_id,
        supersedes=supersedes,
        attachment_sha256=_attachment_digest(
            ucns_identity_sha256=ucns_identity_sha256,
            language_tag=language_tag,
            surface=surface,
            scope=scope,
            source_id=source_id,
            supersedes=supersedes,
        ),
    )


@dataclass(frozen=True, slots=True)
class PolyglotReferent:
    """One UCNS identity plus zero or more external language attachments."""

    ucns_identity_sha256: str
    ucns_schema: str = UCNS_SCHEMA
    ucns_version: str = UCNS_VERSION
    labels: tuple[LabelAttachment, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.ucns_identity_sha256, str) or not _SHA256_RE.fullmatch(
            self.ucns_identity_sha256
        ):
            raise PolyglotError("ucns_identity_sha256 must be a lowercase hexadecimal SHA-256")
        if self.ucns_schema != UCNS_SCHEMA or self.ucns_version != UCNS_VERSION:
            raise PolyglotError("unsupported UCNS identity schema or version")
        if not isinstance(self.labels, tuple):
            raise PolyglotError("labels must be an immutable tuple")

        seen: set[str] = set()
        prior_by_digest: dict[str, LabelAttachment] = {}
        for attachment in self.labels:
            if not isinstance(attachment, LabelAttachment):
                raise PolyglotError("labels must contain LabelAttachment records")
            if attachment.ucns_identity_sha256 != self.ucns_identity_sha256:
                raise PolyglotError("label attachment referent does not match PolyglotReferent")
            if attachment.attachment_sha256 in seen:
                raise PolyglotError("duplicate label attachment identity")
            if attachment.supersedes is not None:
                prior = prior_by_digest.get(attachment.supersedes)
                if prior is None:
                    raise PolyglotError("supersedes must reference an earlier attachment on this referent")
                if prior.language_tag != attachment.language_tag:
                    raise PolyglotError("supersession must stay within one language")
            seen.add(attachment.attachment_sha256)
            prior_by_digest[attachment.attachment_sha256] = attachment

    @property
    def referent_identity(self) -> str:
        """The stable identity is exactly the consumed UCNS identity."""

        return self.ucns_identity_sha256

    def current_labels(
        self,
        *,
        language_tag: str | None = None,
        scope: str | None = None,
    ) -> tuple[LabelAttachment, ...]:
        """Return attachments not superseded by a later attachment."""

        superseded = {
            attachment.supersedes
            for attachment in self.labels
            if attachment.supersedes is not None
        }
        result = []
        for attachment in self.labels:
            if attachment.attachment_sha256 in superseded:
                continue
            if language_tag is not None and attachment.language_tag != language_tag:
                continue
            if scope is not None and attachment.scope != scope:
                continue
            result.append(attachment)
        return tuple(result)

    def as_dict(self) -> dict[str, object]:
        return {
            "ucns_identity_sha256": self.ucns_identity_sha256,
            "ucns_schema": self.ucns_schema,
            "ucns_version": self.ucns_version,
            "labels": [attachment.as_dict() for attachment in self.labels],
        }


def attach_label(
    referent: PolyglotReferent,
    attachment: LabelAttachment,
) -> PolyglotReferent:
    """Return the same referent identity with one additional label attachment."""

    if not isinstance(referent, PolyglotReferent):
        raise PolyglotError("referent must be a PolyglotReferent")
    if not isinstance(attachment, LabelAttachment):
        raise PolyglotError("attachment must be a LabelAttachment")
    return PolyglotReferent(
        ucns_identity_sha256=referent.ucns_identity_sha256,
        ucns_schema=referent.ucns_schema,
        ucns_version=referent.ucns_version,
        labels=referent.labels + (attachment,),
    )


def same_referent(first: PolyglotReferent, second: PolyglotReferent) -> bool:
    """Compare only the underlying UCNS identity, never the attached labels."""

    if not isinstance(first, PolyglotReferent) or not isinstance(second, PolyglotReferent):
        raise PolyglotError("same_referent requires PolyglotReferent values")
    return first.ucns_identity_sha256 == second.ucns_identity_sha256


__all__ = [
    "UCNS_SCHEMA",
    "UCNS_VERSION",
    "LabelAttachment",
    "PolyglotError",
    "PolyglotReferent",
    "attach_label",
    "build_label_attachment",
    "same_referent",
]
