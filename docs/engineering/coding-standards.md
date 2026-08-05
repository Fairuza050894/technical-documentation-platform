# Coding Standards

## Backend

- Python 3.12.
- Type hints are required for public functions and methods.
- Ruff handles formatting and linting.
- Mypy runs in strict mode.
- Pydantic models validate external boundaries only.
- Domain entities protect invariants and do not depend on frameworks.
- Stable error codes are required for expected failures.
- Structured logs must not include credentials or secret values.

## Frontend

- TypeScript strict mode.
- React components use explicit props and accessible HTML semantics.
- Avoid `any`; justify unavoidable exceptions locally.
- Keep remote server state separate from transient UI state.
- Use internal design tokens instead of ad-hoc values.
- Do not use color as the only status indicator.
- Avoid decorative charts, gradients, glassmorphism, excessive radius, and generic AI-product language.
- Keep `App.tsx` as a composition root; application chrome and route content belong in app-layer components.
- Product modules must not render or import global application-shell components.
- `globals.css` is an import manifest; new selectors belong in the layer that owns their responsibility.
- CSS comments describe responsibility or constraints, not patch history.
- Preserve controlled CSS import order unless visual regression review approves a cascade change.

## General

- Prefer composition over inheritance.
- Keep changes small and independently reviewable.
- Tests should assert behavior, not implementation details.
- Comments explain decisions or constraints, not obvious syntax.

## Request identity

- Mutation endpoints must derive identity from the server-side request principal.
- Client request bodies must not contain free-text actor or approver identity fields.
- Local development identities must be marked with development assurance and must not be enabled in staging or production.
- Audit records must preserve a stable actor snapshot and must not log tokens or credentials.

## Runtime configuration

- Environment-specific URLs, paths, origins, identity settings, and limits must be loaded from environment configuration.
- Tracked `.env.example` files document names and safe examples only.
- Real `.env` files and secrets must remain outside Git.
- Production startup must fail closed when required security configuration is missing or an unsafe development provider is selected.

## Documentation as code

- Material behavior, architecture, security, user-flow, operational, or release changes require documentation updates.
- Human-governed documents must not be silently rewritten by automation.
- Generated repository indexes must be changed only through `make docs`.
- Generated documentation must be deterministic and contain no local paths, timestamps, credentials, or runtime data.
- `make docs-check` must pass before commit.
- Standards references describe intended alignment and must not imply certification or legal approval.
- Repository documentation, system templates, and user-generated project documents are separate information classes.
