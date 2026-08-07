# MVP 1 Shared Button CSS Ownership

## Purpose

Make `components.css` the canonical owner for reusable button baselines and global button states
without changing current button behavior or presentation.

## Canonical selectors

- `.button`;
- `.button:disabled`;
- `.button--primary`;
- `.button--primary:hover:not(:disabled)`;
- `.button--primary:disabled`;
- `.button--secondary`;
- `.button--secondary:hover:not(:disabled)`;
- `.button--quiet`;
- `.button--quiet:hover:not(:disabled)`;
- `.button--danger-quiet`;
- `.button--danger-quiet:hover:not(:disabled)`.

## Rules

1. `components.css` owns the reusable button baseline and global semantic states.
2. `foundation.css` must not contain unscoped button-family baseline declarations.
3. `overview.css` must not define global button disabled states.
4. Contextual descendant rules may remain where they express layout responsibility, including:
   - catalog toolbar full-width actions at narrow widths;
   - workspace filter action placement;
   - page-action responsive width;
   - notice action placement;
   - Project Workbench next-action layout.
5. The effective disabled palette that existed before this migration is preserved.
6. No JSX, click behavior, disabled conditions, API contract, route, domain rule, or data model is
   changed.
7. Button redesign, token redesign, and contextual-layout migration are outside this slice.

## Acceptance criteria

- canonical global button selectors exist in `components.css`;
- no equivalent unscoped global button baseline remains in `foundation.css` or `overview.css`;
- primary and generic disabled buttons retain their current neutral disabled appearance;
- secondary, quiet, danger-quiet, hover, and enabled primary states retain current appearance;
- contextual responsive button layout remains unchanged;
- duplicate selector count decreases from the B2A1 baseline of 71;
- repository quality gates, generated documentation, production build, and whitespace checks pass.
