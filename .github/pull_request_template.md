## Summary

Describe the problem, the chosen solution, and the user or system outcome.

## Scope

- [ ] Product behavior
- [ ] Architecture or domain model
- [ ] API or frontend route
- [ ] Security or identity boundary
- [ ] Persistence or migration
- [ ] Documentation or governance
- [ ] Test-only or tooling change

## Traceability

- Requirement or issue:
- ADR:
- Affected documents:
- Evidence or fixture:
- Risk or compatibility note:

## Verification

- [ ] `make docs` was run when applicable.
- [ ] Generated documentation diff was reviewed.
- [ ] `make docs-check` passes.
- [ ] `make verify` passes.
- [ ] `git diff --check` passes.
- [ ] No `.env`, runtime database, imported artifact, generated customer document, credential, or secret is included.
- [ ] Loading, empty, success, and error states are covered when user-facing behavior changes.
- [ ] Known limitations and residual risks are documented.

## Screenshots or evidence

Include only non-sensitive evidence. Remove credentials, customer data, and private artifacts.

## Approval notes

Repository merge is not formal production, legal, security, or compliance approval unless the authorized role records that decision separately.
