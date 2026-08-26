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

### Component patterns

- One component per file; small helper components may co-locate with their parent.
- Props interface defined directly above the component function.
- Use `useCallback` for event handlers passed to child components.
- Use `useMemo` for derived state and filtered lists.
- Always pass `AbortController.signal` to async operations in `useEffect`.
- Cleanup async operations in `useEffect` return function.

### State management

- Local state with `useState`; no global state library.
- `localStorage` for persistence preferences (workspace selection, sidebar collapse).
- Filter state co-located with the list it filters.

### Error handling

- Application-level `ErrorBoundary` wraps the entire app in `main.tsx`.
- Domain-specific `ConfirmDialog` for destructive workflow actions.
- Error responses use consistent `{ error: { code, message, details, requestId } }` shape.
- Loading states use `role="status"` for screen reader announcement.

### Accessibility

- Semantic HTML elements preferred over generic `div`.
- `aria-label` on all landmarks (`<aside>`, `<nav>`, `<main>`, `<header>`).
- `aria-current="page"` on active navigation items.
- `role="status"` on loading indicators.
- `role="alert"` on error messages.
- Skip-to-content link for keyboard navigation.
- `prefers-reduced-motion: reduce` disables animations and transitions.
- Focus ring via `--focus-ring` custom property on all interactive elements.

### CSS organization

- Design tokens in `styles/tokens.css` (colors, spacing, radii, shadows).
- Global reset and base styles in `styles/foundation.css`.
- Shared component primitives in `styles/components.css`.
- Application shell layout in `styles/application-shell.css`.
- Module-specific styles in `styles/modules/<name>.css`.
- Print styles in `@media print` block within `application-shell.css`.
- New CSS classes follow BEM-like convention: `.block__element--modifier`.


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
