name: uchc
description: |
  Implementation repository for Unit Circle Hyperspace Constructs across human
  and programming-language domains.

# UCHC agent instructions

Before changing this repository, resolve current The-Interdependency/skill-lib and
load every applicable skill. The scaffold baseline used
`skill-lib@9a04120686ee4e03338eaf14a81073e467aecfe8`.

## Authority

- UCHC owns language-hyperspace implementation and public contracts only after a
  domain has been migrated here and verified.
- UCNS owns gonol objects, constructors, Public Gonol carrier geometry, Möbius
  geometry, and other UCNS geometry. Consume it; do not shadow it.
- METAPAT owns affixiation semantics where consumed.
- Stack is the current forge for English and Python until their migration gates pass.
- EDCM measures/evaluates; it does not define UCHC construction.
- Consumer apps remain separate repositories. They may project UCHC; they may not
  manufacture canonical UCHC relations.

## Structure

`human/<language>/` and `programming/<language>/` are implementations, not
descriptive namespaces over some hidden implementation layer.

Do not add a shared geometry `core/` that competes with UCNS. Shared code belongs
here only when it is genuinely UCHC implementation and not upstream UCNS geometry.

## Migration rule

Move one live domain at a time from its exact pinned Stack source. Preserve tests,
receipts, source identity, order, multiplicity, relations, provenance, and hmmm.
Require replay/equivalence evidence before changing Stack from forge to consumer.

Forthcoming domains contain no speculative implementation.

## Usage guidance

For implementation work, start from `docs/MIGRATION.md`, then the relevant domain
README. For geometry changes, stop here and repair UCNS instead. For consumer-app
changes, work in the consumer repository.

## hmmm

- repository license;
- release/distribution surface;
- full repo-local skill-lib propagation;
- unresolved geometry inherited from UCNS or the active domain.
