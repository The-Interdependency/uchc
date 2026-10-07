# Polyglot identity layer

## Purpose

UCHC attaches language surfaces to a stable UCNS geometric identity.

The referent is not a word and is not a translation pair. It is the UCNS
identity produced by the axis-circle position candidate. UCHC records language,
register/scope, provenance, and label history around that referent.

    UCNS position identity
        <- English label
        <- Spanish label
        <- technical label
        <- historical label

The arrows are attachments to one referent, not pairwise equality assertions.

## Rename behavior

A later label may supersede an earlier attachment while preserving both records.

Example:

    heart -> same UCNS identity
    cardiac -> same UCNS identity, supersedes heart

The referent identity does not change.

## Multiple languages

Independent language implementations may attach their own surfaces:

    cardiac  (en)
    cardíaco (es)
    cardiaque (fr)

Sharing a referent does not claim that these strings have identical lexical
partitioning in every context. Language-specific construction and admission
remain owned by each language implementation.

## Usage guidance

    from uchc_polyglot import (
        PolyglotReferent,
        attach_label,
        build_label_attachment,
    )

    referent = PolyglotReferent(ucns_identity_sha256=position.identity_sha256)
    referent = attach_label(
        referent,
        build_label_attachment(
            ucns_identity_sha256=position.identity_sha256,
            language_tag="en",
            surface="cardiac",
            scope="technical",
            source_id="source:example",
        ),
    )

The caller obtains position.identity_sha256 from UCNS. UCHC does not recompute
or redefine the geometry.

## Authority boundary

- UCNS owns the geometric position and its identity.
- UCHC owns language-scoped attachments and their history.
- A language implementation owns its source/admission/construction evidence.
- METAPAT domain restraint prevents shared structure from silently transferring
  domain-specific meaning.
- EDCM may later measure constructed outputs; it does not define the relation.

## hmmm

Language-specific semantic partitioning, admission profiles, and evidence for
particular cross-language referent attachments remain separate work. Shared
geometric identity makes the relation representable; it does not make every
dictionary translation exact.
