# === CHECKS ===
# id: check_polyglot_referent_identity_is_ucns_identity
#   proves: polyglot_referent_identity_is_ucns_identity
#   call: self::test_rename_preserves_ucns_referent
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_polyglot_labels_are_scoped_attachments
#   proves: polyglot_labels_are_scoped_attachments
#   call: self::test_multiple_languages_attach_to_one_referent
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_polyglot_does_not_assert_pairwise_translation_identity
#   proves: polyglot_does_not_assert_pairwise_translation_identity
#   call: self::test_labels_share_referent_without_pairwise_equality
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_polyglot_supersession_preserves_history
#   proves: polyglot_supersession_preserves_history
#   call: self::test_supersession_preserves_history
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_polyglot_fails_closed
#   proves: polyglot_fails_closed
#   call: self::test_polyglot_fails_closed
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
# === END CHECKS ===

import pytest

from uchc_polyglot import (
    PolyglotError,
    PolyglotReferent,
    attach_label,
    build_label_attachment,
    same_referent,
)


UCNS_ID = "a" * 64


def test_rename_preserves_ucns_referent() -> None:
    referent = PolyglotReferent(ucns_identity_sha256=UCNS_ID)
    heart = build_label_attachment(
        language_tag="en",
        surface="heart",
        scope="ordinary",
        source_id="thread:initial",
    )
    first = attach_label(referent, heart)
    cardiac = build_label_attachment(
        language_tag="en",
        surface="cardiac",
        scope="technical",
        source_id="thread:rename",
        supersedes=heart.attachment_sha256,
    )
    renamed = attach_label(first, cardiac)

    assert first.referent_identity == UCNS_ID
    assert renamed.referent_identity == UCNS_ID
    assert same_referent(first, renamed)
    assert [item.surface for item in renamed.current_labels()] == ["cardiac"]


def test_multiple_languages_attach_to_one_referent() -> None:
    referent = PolyglotReferent(ucns_identity_sha256=UCNS_ID)
    for language, surface in (
        ("en", "cardiac"),
        ("es", "cardíaco"),
        ("fr", "cardiaque"),
    ):
        referent = attach_label(
            referent,
            build_label_attachment(
                language_tag=language,
                surface=surface,
                scope="technical",
                source_id=f"fixture:{language}",
            ),
        )

    assert referent.referent_identity == UCNS_ID
    assert [item.surface for item in referent.current_labels(language_tag="es")] == ["cardíaco"]
    assert len(referent.current_labels()) == 3


def test_labels_share_referent_without_pairwise_equality() -> None:
    english = build_label_attachment(
        language_tag="en",
        surface="cardiac",
        scope="technical",
        source_id="fixture:en",
    )
    spanish = build_label_attachment(
        language_tag="es",
        surface="cardíaco",
        scope="technical",
        source_id="fixture:es",
    )
    referent = PolyglotReferent(
        ucns_identity_sha256=UCNS_ID,
        labels=(english, spanish),
    )
    payload = referent.as_dict()

    assert english.surface != spanish.surface
    assert payload["ucns_identity_sha256"] == UCNS_ID
    assert "translation" not in payload
    assert "equals" not in payload


def test_supersession_preserves_history() -> None:
    ordinary = build_label_attachment(
        language_tag="en",
        surface="heart",
        scope="focus-locus",
        source_id="fixture:v1",
    )
    technical = build_label_attachment(
        language_tag="en",
        surface="cardiac",
        scope="focus-locus",
        source_id="fixture:v2",
        supersedes=ordinary.attachment_sha256,
    )
    referent = PolyglotReferent(
        ucns_identity_sha256=UCNS_ID,
        labels=(ordinary, technical),
    )

    assert [item.surface for item in referent.labels] == ["heart", "cardiac"]
    assert [item.surface for item in referent.current_labels()] == ["cardiac"]


def test_polyglot_fails_closed() -> None:
    with pytest.raises(PolyglotError):
        PolyglotReferent(ucns_identity_sha256="not-a-digest")

    first = build_label_attachment(
        language_tag="en",
        surface="heart",
        scope="ordinary",
        source_id="fixture:1",
    )
    dangling = build_label_attachment(
        language_tag="en",
        surface="cardiac",
        scope="technical",
        source_id="fixture:2",
        supersedes="b" * 64,
    )
    with pytest.raises(PolyglotError):
        PolyglotReferent(
            ucns_identity_sha256=UCNS_ID,
            labels=(first, dangling),
        )

    with pytest.raises(PolyglotError):
        PolyglotReferent(
            ucns_identity_sha256=UCNS_ID,
            labels=(first, first),
        )
