# MVP 1 Registry and Technical Intake CSS Ownership

## Purpose

Move registry and technical-intake workspace composition out of shared/global compatibility files
and into explicit module owners.

This batch covers Workspaces, Features, Sources, and API Catalog together because they form the
project setup and technical-intake journey.

## Result

- `modules/workspaces.css` remains the owner for workspace selector/registry composition.
- `modules/features.css` remains the owner for Feature/Module Registry and Documentation Map.
- `modules/sources.css` becomes the owner for Source Registry filtering and source metadata details.
- `modules/catalog.css` becomes the owner for API Catalog controls, operation layout, and evidence
  presentation.
- `components.css` retains only reusable form, table, button, page, feedback, and status primitives.
- `foundation.css` no longer owns Source or API Catalog module classes.
- `overview.css` no longer acts as a responsive compatibility bucket for Source/API Catalog.

## Preserved effective behavior

The migration preserves the computed behavior that previously depended on cascade order, including:

- Source filter desktop and narrow-screen grid behavior;
- checksum secondary metadata styling;
- API Catalog toolbar density and responsive collapse;
- operation/evidence two-column desktop layout;
- selected operation row styling;
- sticky evidence panel and narrow-screen static behavior;
- HTTP method badge;
- source-reference truncation.

## Non-goals

This batch does not redesign Workspaces, Features, Sources, or API Catalog. It does not change JSX,
routing, API contracts, domain rules, persistence, tokens, or typography.

Documents/Changes migration remains B3B. Operational Overview/app-shell residual cleanup remains B3C.

## Acceptance criteria

- Source-only classes are owned only by `modules/sources.css`;
- API Catalog-only classes are owned only by `modules/catalog.css`;
- import manifest explicitly includes both module files;
- existing Workspaces and Features ownership remains intact;
- duplicate CSS selector-name count decreases from 48 to 43 or lower;
- focused target-module tests pass;
- repository documentation, full quality gate, production build, and whitespace checks pass.
