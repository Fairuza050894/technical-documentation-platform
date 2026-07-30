# MVP 1 Visual Refinement R2

## Goal

Complete the final visual and language cleanup before the project-centric workbench starts.

## Requirements

1. Navigation changes reset the document scroll position so page headers and actions are not hidden below the sticky utility bar.
2. The UI maps the internal `SUPERSEDED` lifecycle value to the user-facing label `Replaced`; backend contracts remain unchanged.
3. A replaced version identifies the next newer version when it is available.
4. Version counts use correct singular and plural forms.
5. Attention counts describe conditions instead of showing an unexplained number.
6. The API catalog selects the most recently updated ready source by default and identifies each operation's source.
7. Disabled actions are visually neutral and cannot be confused with enabled primary actions.
8. Document generation uses a compact revision-reason field.
9. Existing backend lifecycle behavior, immutable versioning, and API compatibility remain unchanged.

## Quality gates

- `git diff --check` passes.
- Frontend lint, tests, and production build pass.
- The visual-refinement audit records the R2 markers.
- No file is staged, committed, or pushed by the installer.
