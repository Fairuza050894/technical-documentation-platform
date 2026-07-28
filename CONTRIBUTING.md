# Contributing

## Change workflow

All code changes should be delivered and applied as focused unified-diff patches.

```bash
git apply --check path/to/change.patch
git apply path/to/change.patch
make verify
git status --short
git diff --check
git diff
```

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

## Engineering rules

- Domain code must not import FastAPI, SQLAlchemy, or frontend concerns.
- HTTP controllers must not contain business rules.
- Infrastructure implementations depend on application ports, not the reverse.
- Do not return ORM models directly from APIs.
- Do not introduce generic base services or repositories without a proven repeated need.
- Every user-facing flow must include loading, empty, success, and failure states.
- Generated documentation must preserve source provenance.
- Missing facts must be marked as missing; they must never be invented.
