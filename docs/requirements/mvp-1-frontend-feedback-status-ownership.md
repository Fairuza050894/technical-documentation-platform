# MVP 1 Feedback and Status CSS Ownership

## Purpose

Consolidate shared feedback and status primitives under `components.css` while preserving the
effective visual behavior already used across project, workbench, catalog, changes, and document
workspaces.

This slice intentionally combines the former B2B1 and B2B2 work because they share one canonical
owner, one visual vocabulary, and one repository quality gate.

## Canonical responsibilities

`components.css` owns:

- notice baseline, error, warning, icon, body, code treatment, and narrow-width notice layout;
- environment badge baseline, semantic states, and environment badge dot;
- record count and status label;
- status indicator baseline and semantic states;
- document status badge baseline and semantic states;
- change-kind baseline and semantic states.

## Contextual exceptions

Module files may retain scoped rules where the selector is part of a module-specific composition.
For example, `changes.css` may adjust `.status-indicator` only under `.changes-results`.

`application-shell.css` continues to own service/runtime dots, but not the reusable environment
badge dot.

## Compatibility rules

1. No intentional visual redesign is introduced.
2. Archived-project warning keeps its current warning palette and layout.
3. Error notices keep their current danger palette.
4. Environment badges keep the current pill geometry and dot behavior.
5. Status indicators keep their existing compact legacy geometry until a later intentional visual
   redesign.
6. Historical/superseded document status keeps the current neutral visual treatment.
7. Change-kind semantics retain their current success/info/danger treatments.
8. No JSX, status value, API contract, route, domain rule, or database model changes are introduced.

## Acceptance criteria

- legacy unscoped feedback/status baselines are absent from `foundation.css`;
- global feedback/status rules no longer leak from `overview.css`;
- environment badge dot ownership no longer leaks from `application-shell.css`;
- reusable feedback/status primitives resolve from `components.css`;
- scoped Changes Workspace status-indicator behavior remains intact;
- duplicate CSS selector-name count decreases from the B2A2 baseline of 67 to 52 or lower;
- repository documentation is current;
- all backend/frontend quality gates and production build pass;
- whitespace checks pass.
