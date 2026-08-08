# MVP 1 Table and Page Primitive CSS Ownership

## Purpose

Consolidate shared table and page hierarchy primitives under `components.css` while preserving the
effective visual contract that existed before the migration.

Tables and page primitives are combined in one slice because they are mature reusable UI
foundations, already have shared component definitions, and can be verified in one cross-route
quality gate.

## Canonical ownership

`components.css` owns the shared baseline for:

- topbar;
- eyebrow;
- content section;
- section heading and split heading;
- table frame;
- table secondary text;
- table action column;
- empty state.

## Effective behavior preserved

Properties previously surviving only because `foundation.css` loaded first are explicitly retained
in the canonical owner:

- topbar divider and bottom padding;
- table-frame low shadow;
- table secondary-text maximum width and ellipsis;
- `td strong` block behavior;
- empty-state top spacing;
- empty-state headings for both `h2` and `h3`.

Global table-frame cell colors and topbar responsive behavior that previously leaked from
`overview.css` also move into `components.css`.

## Valid contextual overrides

Module-specific composition remains module-owned, including:

- Workbench embedded content-section spacing;
- Workbench header eyebrow adjustment;
- Overview operations empty-state treatment;
- document-section heading/table/empty-state composition;
- Feature Registry table spacing.

## Non-goals

No sidebar/app-shell cleanup, module redesign, token or typography redesign, product behavior, API,
routing, domain, or persistence changes are introduced.

## Acceptance criteria

- shared unscoped baselines are absent from `foundation.css`;
- global topbar/table-frame cell rules no longer leak from `overview.css`;
- current desktop and responsive presentation is preserved;
- valid contextual module overrides remain;
- duplicate selector count decreases from 52 to 48 or lower;
- generated documentation and all repository quality gates pass;
- whitespace checks pass.
