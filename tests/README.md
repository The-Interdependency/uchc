# Tests

This directory will hold UCHC cross-domain and repository-level conformance tests.

Domain-local tests migrate with their implementations first.

Repository-level gates should eventually prove:

- identity preservation;
- lossless promotion/recovery where claimed;
- order and multiplicity preservation;
- provenance preservation;
- fail-closed malformed input;
- exact upstream identity binding;
- deterministic replay/receipts where claimed;
- consumer boundaries do not redefine canonical structure.

No passing test is claimed by this scaffold.

hmmm: executable repository-level gates begin with the first migrated implementation.
