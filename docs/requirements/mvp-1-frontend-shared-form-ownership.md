# MVP 1 Shared Form CSS Ownership

## Purpose

Move reusable form-class ownership from the legacy `foundation.css` compatibility layer to
`components.css` without changing current computed behavior.

## Scope

The canonical shared-component owner covers:

- `form-panel`;
- `form-grid`;
- `field`;
- `field--wide`;
- `form-error`;
- `form-actions`;
- `inline-actions`.

Element-level `input`, `select`, and `textarea` migration is intentionally deferred because those
rules have a separate element-baseline compatibility contract.

## Rules

1. `components.css` is the canonical owner for reusable form classes.
2. `foundation.css` must not contain unscoped declarations for the shared form classes above.
3. Module CSS may keep contextual descendant overrides when they express module-specific layout.
4. Existing effective spacing, typography, responsive behavior, and validation color remain
   unchanged.
5. No form JSX, API contract, routing behavior, domain rule, or data model changes are introduced.
6. Button ownership is handled separately in B2A2 because its disabled and contextual states have
   wider cascade dependencies.

## Acceptance criteria

- all seven shared form selectors resolve from `components.css`;
- their legacy unscoped declarations are absent from `foundation.css`;
- duplicate selector count decreases from the B1 baseline of 75;
- Create Workspace, Create Project, Feature/Module, Source import, Changes comparison, and Document
  forms retain their current visual layout;
- frontend tests, backend tests, lint, type checks, production build, documentation checks, and
  whitespace checks pass.
