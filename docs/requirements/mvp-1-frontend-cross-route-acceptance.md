# MVP 1 Final Cross-Route Frontend Acceptance

## Purpose

Close MVP 1 frontend hardening with a cross-route acceptance sweep after canonical CSS ownership
has been established.

B4 is acceptance-driven. It must not reopen broad CSS refactoring. Code changes after this point are
allowed only when a demonstrated regression is discovered by the sweep.

## Acceptance matrix

### Desktop

Verify the current desktop presentation for:

- Home / Operational Overview;
- Projects registry;
- Project Workbench Overview;
- Features;
- Sources;
- API Catalog;
- Changes;
- Documents;
- System Status.

### Approximately 900 px

Verify:

- sidebar remains usable;
- workspace canvas and utility bar do not overlap;
- project stage navigation remains readable and horizontally usable where required;
- tables do not force destructive page overflow;
- action controls remain reachable.

### Approximately 760 px

Verify:

- shell changes to the existing stacked presentation;
- primary navigation remains horizontally scrollable;
- utility runtime metadata hides according to the existing responsive contract;
- System Status and shared form grids collapse to one column;
- Overview, Workbench, Sources, Catalog, Changes, and Documents remain usable.

### Long values

Exercise representative long values:

- Workspace and Project names;
- source names and checksums;
- API paths and summaries;
- feature/module names;
- document titles, revision reasons, and comparison excerpts.

Long values must wrap, truncate, or scroll according to the established component contract rather
than overlap adjacent content.

### Archived/read-only project

Verify:

- archived project remains discoverable and openable;
- existing evidence, catalog, features, changes, documents, versions, review history, and audit
  information remain readable;
- archived warning is visible;
- mutation controls remain blocked;
- navigation/deep links remain usable.

### Navigation state

Verify:

- deep-link refresh restores Workspace, Project, Feature/Module where applicable, and Workbench
  stage;
- browser Back and Forward restore the previous route context;
- changing Workspace returns to that Workspace context without silently replacing it with a
  Project selector;
- project/stage navigation does not lose the selected Workspace.

## Automated evidence

B4 reuses the existing application/router/navigation/workbench/workspace tests and runs the full
repository quality gate. The audit also verifies that the CSS duplicate-selector count does not
regress above the B3C baseline of 11.

## Non-goals

B4 does not introduce:

- a new visual design;
- token or typography redesign;
- dark mode;
- new mobile navigation;
- new product features;
- API/domain/persistence changes;
- cleanup performed solely to reduce duplicate-selector count.

## Exit criteria

MVP 1 frontend hardening is complete when:

- focused route/context tests pass;
- full repository verification and production build pass;
- duplicate selector count is 11 or lower;
- whitespace is clean;
- the manual visual/behavior matrix is accepted;
- no unresolved regression remains from the ownership migration.
