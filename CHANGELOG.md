# Changelog

All notable changes to the Technical Documentation Platform are recorded here.

The project will follow semantic versioning when formal release tags begin. Until then, entries are grouped under **Unreleased** and linked to repository commits.

## Unreleased

### Added

- explicit frontend application-shell, route-content, navigation, and runtime boundaries;
- ordered CSS responsibility layers with architecture fitness checks;
- Frontend Composition audit and ADR-017;

- living repository documentation governance;
- canonical product, architecture, quality, compliance, operations, release, and user-guide documents;
- deterministic repository documentation generator and freshness check;
- generated repository, ADR, requirement, API, route, test, and document indexes;
- GitHub CODEOWNERS, pull-request template, and issue templates;
- external audit management response;
- reviewer reconciliation for enterprise document types and automation boundaries.

### Changed

- `App.tsx` reduced to a stateful composition root while preserving routes and behavior;
- `globals.css` converted to an ordered import manifest without intentional visual changes;

- root README converted from chronological slice log to a concise product and documentation portal;
- `make verify` now includes repository documentation freshness;
- product roadmap and audit dispositions now distinguish completed, partially addressed, open,
  deferred, and dependency-blocked work.

## Historical foundation

The repository history before formal release tagging includes:

- engineering foundation;
- project and workspace management;
- OpenAPI source management;
- API catalog synchronization;
- deterministic change detection;
- Technical Source Overview generation;
- document lifecycle and version comparison;
- operational product UI;
- project-centric workbench;
- Feature or Module Registry;
- Engineering Safety Baseline.
