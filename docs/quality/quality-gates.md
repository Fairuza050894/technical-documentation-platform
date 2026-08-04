# Quality Gates

| Field | Value |
|---|---|
| Document ID | TDP-QUAL-002 |
| Status | Controlled draft |
| Owner | Quality Engineering |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Required local gate

```bash
make docs-check
make verify
git diff --check
```

## `make verify`

| Gate | Purpose |
|---|---|
| Repository documentation check | Required docs, metadata, links, and generated freshness |
| Ruff lint | Python correctness and consistency |
| Ruff format check | Deterministic Python formatting |
| Mypy strict | Backend type safety |
| Pytest | Backend behavior and architecture |
| ESLint | Frontend correctness and safety |
| Vitest | Frontend behavior |
| Backend import validation | Composition-root startup |
| Frontend production build | TypeScript and bundle validation |

## CI behavior

GitHub Actions runs the same `make verify` command for pull requests and pushes to `main`. CI is read-only and does not modify or commit documentation.

## Failure handling

A gate must not be bypassed by deleting tests, weakening lint configuration, or excluding relevant files. Exceptions require:

```text
documented reason
scope
risk
owner
expiry or review condition
approval
```

## Dedicated audits

Audit scripts write one complete report to `~/Downloads`, exclude runtime evidence and secrets, and preserve the command outputs used for review.
