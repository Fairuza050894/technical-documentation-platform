# Contributing

## Change workflow

Changes must be focused, reviewable, and traceable.

```bash
git apply --check path/to/change.patch
git apply path/to/change.patch
make docs
make verify
git status --short
git diff --check
git diff
```

`make docs` is required when code, APIs, routes, modules, tests, ADRs, requirements, governance, or release information changes. Generated files must be reviewed and committed; CI never commits generated documentation automatically.

After verification:

```bash
git add <relevant-files>
git commit -m "<type>(<scope>): <summary>"
```

## Commit convention

Use Conventional Commit-style messages:

- `feat(projects): add project creation`
- `fix(sources): reject invalid OpenAPI files`
- `refactor(catalog): isolate endpoint normalization`
- `test(changes): cover required-field breaking change`
- `docs(architecture): record snapshot strategy`
- `chore(tooling): configure quality gates`

## Documentation change classification

Update the appropriate controlled document when a change affects:

- product scope, stakeholder outcomes, or user flow;
- domain boundaries, integrations, persistence, security, or deployment;
- functional or non-functional requirements;
- controls, risks, ownership, approval, or retention;
- public API, frontend routes, test coverage, or release readiness.

Human-governed documents require human review. Generated indexes must only be changed through `make docs`.

## Engineering rules

- Domain code must not import FastAPI, SQLite, or frontend concerns.
- HTTP controllers must not contain business rules.
- Infrastructure implementations depend on application ports, not the reverse.
- Do not return persistence models directly from APIs.
- Do not introduce generic abstractions without a proven repeated need.
- Every user-facing flow must include loading, empty, success, and failure states.
- Generated documentation must preserve source provenance.
- Missing facts must be marked as missing; they must never be invented.
- Mutation identity must come from the server-resolved request principal.
- Secrets, credentials, imported customer evidence, and runtime artifacts must not enter Git.

## Pull requests

Use the repository pull-request template. A change is not ready for review until:

```bash
make docs-check
make verify
git diff --check
```

all pass locally.
