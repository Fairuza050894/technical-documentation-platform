
# MVP 1 Engineering Safety Baseline

## Objective

Make quality gates, runtime configuration, request identity, and system health
explicit and reproducible before governed Requirement and version-decision
features are added.

## Functional requirements

1. GitHub Actions runs `make verify` for pull requests and pushes to `main`.
2. Frontend API requests use `VITE_API_BASE_URL` and contain no hardcoded
   localhost backend URL.
3. Vite proxies same-origin `/api` requests to the local backend during
   development.
4. Backend and frontend provide tracked `.env.example` files without secrets.
5. The backend exposes a framework-independent `RequestPrincipal`.
6. Document generation and workflow mutations derive the actor from the
   server-resolved principal.
7. Client-supplied `actor` fields are rejected.
8. The local principal is permitted only in `development` and `test`.
9. Shared environments fail configuration validation while local identity is
   selected.
10. `/api/identity/me` exposes the current principal and assurance level.
11. `/api/health/live` reports process liveness.
12. `/api/health/ready` checks SQLite and the artifact directory.
13. Existing `/api/health` remains backward compatible.
14. API responses include baseline security headers.
15. `SECURITY.md` documents current boundaries and private reporting guidance.
16. A dedicated audit writes one complete report to Downloads.

## Non-goals

- OIDC or JWT token validation.
- Role-based authorization.
- Workspace membership.
- PostgreSQL or explicit schema migration framework.
- Public internet deployment.
- Legal-grade non-repudiation.
- Containerization.

## Acceptance criteria

- No document mutation request model accepts an actor field.
- Workflow history records the configured principal snapshot.
- Production and staging configuration reject local identity mode.
- No frontend source contains `127.0.0.1:8000`.
- CI, backend lint, formatting, typing, tests, frontend lint, tests, and build
  pass.
- `.env`, SQLite data, runtime artifacts, imported sources, generated
  documents, and secrets remain outside the patch and audit.
