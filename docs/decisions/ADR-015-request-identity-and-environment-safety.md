
# ADR-015: Request identity and environment safety boundary

- Status: Accepted
- Date: 2026-08-01

## Context

Document workflow mutations currently accept an `actor` string from the client.
That value is not authenticated and can be replaced with any display name.
Frontend API URLs are also tied to localhost, quality gates run only on a
developer workstation, and the health endpoint does not distinguish process
liveness from dependency readiness.

The platform needs a safe application boundary before Requirement revisions,
Change Sets, deterministic version decisions, and official release governance
are introduced.

## Decision

1. Introduce a framework-independent `RequestPrincipal`.
2. Resolve the principal at the HTTP boundary through an `IdentityProvider`.
3. Remove client-supplied actor fields from document generation and workflow
   request bodies.
4. Store a stable rendered identity snapshot in the existing `actor` and
   `created_by` fields until structured identity persistence is introduced.
5. Permit the local identity provider only in `development` and `test`.
6. Reject application startup when local identity is configured for `staging`
   or `production`.
7. Expose the current request identity through `/api/identity/me`.
8. Externalize the frontend API base URL with `VITE_API_BASE_URL`, defaulting to
   the same-origin `/api` contract.
9. Add CI that executes the repository's existing `make verify` quality gate.
10. Add baseline HTTP security headers and separate liveness/readiness routes.

## Consequences

- A client can no longer claim another person's display name in workflow
  mutation payloads.
- Local development remains simple and visibly carries `DEVELOPMENT`
  assurance.
- This decision does not implement OIDC, RBAC, workspace membership, or legal
  non-repudiation. Those remain required before shared production use.
- Existing document tables do not require migration in this patch; identity is
  persisted as a stable actor snapshot.
- Deployments must provide an authenticated identity adapter before selecting
  a shared environment.
