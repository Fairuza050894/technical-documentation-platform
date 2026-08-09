# MVP 1 Documents and Changes CSS Ownership

## Purpose

Make document lifecycle/versioning and deterministic change-result presentation explicit module
responsibilities instead of relying on legacy cascade behavior across foundation, shared components,
and Operational Overview styles.

## Canonical ownership

`modules/documents.css` owns document lifecycle sections, generation state, version metadata, detail
panels, workflow timeline/actions, preview/disclosure, version comparison composition, and
document-specific comparison controls.

`modules/changes.css` owns deterministic Changes Workspace result cards and change-result
composition.

Reusable buttons, forms, tables, notices, page primitives, and semantic status badges remain in
`components.css`.

## Cross-module dependency removal

`DocumentsWorkspace` must not depend on Source or API Catalog module classes merely for styling.
The previous `workspace-filter`, `checksum-text`, and `catalog-toolbar__action` usages are replaced
with document-specific presentation classes while preserving behavior.

## Compatibility

- metadata remains three columns desktop, two medium, one narrow;
- document panels retain the current effective spacing, radius, border, surface, and shadow;
- version comparison retains the current compact toolbar and segmented summary;
- long excerpts/checksums keep the current compact presentation;
- workflow timeline and document preview remain unchanged;
- Changes result cards retain their current visual treatment;
- no API, domain, route, workflow-state, persistence, or interaction behavior changes.

## Non-goals

Operational Overview/application-shell residual ownership remains B3C. This slice does not redesign
Documents/Changes, tokens, typography, or product behavior.

## Acceptance criteria

- document-specific classes have one owner: `modules/documents.css`;
- `catalog-card` baseline is owned by `modules/changes.css`;
- Documents TSX no longer uses Source/Catalog module presentation classes;
- foundation/components/overview no longer own document composition;
- duplicate selector count decreases from 43 to 35 or lower;
- focused Documents/Changes tests and the full repository quality gate pass.
