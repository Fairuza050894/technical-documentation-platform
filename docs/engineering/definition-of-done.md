# Definition of Done

A change is complete when:

- acceptance criteria are satisfied;
- relevant unit, integration, architecture, frontend, and composition fitness tests pass;
- type checking and linting pass;
- error, loading, and empty states are handled;
- security-sensitive data is not logged or exposed;
- server-side identity and authorization boundaries are preserved;
- product, architecture, requirement, operational, and release documents are updated when affected;
- `make docs` has been run and the generated diff reviewed;
- `make docs-check` passes;
- production build succeeds;
- frontend boundaries and CSS ownership remain within documented limits;
- `git diff --check` reports no whitespace errors;
- runtime data, imported evidence, `.env`, credentials, and secrets are excluded;
- the final patch contains only files relevant to the change;
- known limitations and residual risks are documented.
