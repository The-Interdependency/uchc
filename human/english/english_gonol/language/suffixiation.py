"""Suffixiation: affixiation between already-closed gonols.

Suffixiation is ``G(base); affix; G(suffix)``. The base contributes its
complete closed construction (including the definitions and behavior of its
constituent characters) and the suffix contributes its own closed construction
and suffix-specific behavior. Neither gonol is reopened: the interaction is
resolved from recoverable internal construction, then a normal
``scale="suffix-coupling"`` gonol closes over the two atomic participants.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

from ..gonol import (
    ClosedGonol,
    GonolConstructionError,
    GonolReceipt,
    construct_gonol,
)
from .character_definitions import (
    CharacterDefinitionLayer,
    build_character_definition_layer,
)

SCHEMA = "english-gonol.suffixiation"
VERSION = "v1"
SUFFIX_VOWEL_INITIAL_KEY = "suffix-coupling.vowel-initial"


def _digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class SuffixiationReceipt:
    """One suffixiation between two closed gonols."""

    source_id: str
    base_source_id: str
    suffix_source_id: str
    suffix_bare: str
    suffix_vowel_initial: bool
    final_character_surface: str | None
    preceding_character_surface: str | None
    y_realization: str | None
    coupling_receipt: GonolReceipt
    receipt_digest: str

    def record(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "version": VERSION,
            "source_id": self.source_id,
            "base_source_id": self.base_source_id,
            "suffix_source_id": self.suffix_source_id,
            "suffix_bare": self.suffix_bare,
            "suffix_vowel_initial": self.suffix_vowel_initial,
            "final_character_surface": self.final_character_surface,
            "preceding_character_surface": self.preceding_character_surface,
            "y_realization": self.y_realization,
            "y_resolution_source": (
                "y-character-definition-space"
                if self.y_realization is not None
                else None
            ),
            "coupling_receipt_digest": self.coupling_receipt.receipt_digest,
            "coupling_atomic_id": self.coupling_receipt.gonol.atomic_id,
            "receipt_digest": self.receipt_digest,
        }


def _suffix_vowel_initial(
    suffix: ClosedGonol,
    layer: CharacterDefinitionLayer,
) -> bool:
    for key, value in suffix.carried_options:
        if key == SUFFIX_VOWEL_INITIAL_KEY:
            return value == "true"
    if not suffix.source_units:
        return False
    entry = layer.entries.get(suffix.source_units[0])
    return entry is not None and entry.has_class("vowel")


def suffixiate(
    base: ClosedGonol,
    suffix: ClosedGonol,
    *,
    source_id: str,
    layer: CharacterDefinitionLayer | None = None,
) -> SuffixiationReceipt:
    """Affixiate a closed suffix gonol onto a closed base gonol.

    ``base`` and ``suffix`` must already be closed gonols; only their
    recoverable internal construction is read, never rebuilt. The resolved
    final-y interaction (if any) comes from the ``y`` character gonol's own
    definition-space and the suffix's suffix-specific carried behavior.
    """

    if suffix.scale != "suffix":
        raise GonolConstructionError("suffixiation requires a closed suffix gonol")
    definitions = layer if layer is not None else build_character_definition_layer()

    suffix_bare = "".join(suffix.source_units)
    suffix_vowel_initial = _suffix_vowel_initial(suffix, definitions)

    final_character_surface: str | None = None
    preceding_character_surface: str | None = None
    if base.source_characters:
        final_character_surface = base.source_characters[-1].source_units[0]
        if len(base.source_characters) >= 2:
            preceding_character_surface = base.source_characters[-2].source_units[0]

    y_realization = definitions.final_y_realization(
        final_character_surface,
        preceding_character_surface,
        suffix_bare,
        suffix_vowel_initial,
    )

    coupling = construct_gonol(
        scale="suffix-coupling",
        participants=(base, suffix),
        source_id=source_id,
    )

    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "source_id": source_id,
        "base_source_id": base.source_id,
        "base_atomic_id": base.atomic_id,
        "suffix_source_id": suffix.source_id,
        "suffix_atomic_id": suffix.atomic_id,
        "suffix_bare": suffix_bare,
        "suffix_vowel_initial": suffix_vowel_initial,
        "final_character_surface": final_character_surface,
        "preceding_character_surface": preceding_character_surface,
        "y_realization": y_realization,
        "coupling_receipt_digest": coupling.receipt_digest,
        "coupling_atomic_id": coupling.gonol.atomic_id,
    }
    receipt_digest = _digest_bytes(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return SuffixiationReceipt(
        source_id=source_id,
        base_source_id=base.source_id,
        suffix_source_id=suffix.source_id,
        suffix_bare=suffix_bare,
        suffix_vowel_initial=suffix_vowel_initial,
        final_character_surface=final_character_surface,
        preceding_character_surface=preceding_character_surface,
        y_realization=y_realization,
        coupling_receipt=coupling,
        receipt_digest=receipt_digest,
    )


__all__ = ["SCHEMA", "SUFFIX_VOWEL_INITIAL_KEY", "SuffixiationReceipt", "VERSION", "suffixiate"]
