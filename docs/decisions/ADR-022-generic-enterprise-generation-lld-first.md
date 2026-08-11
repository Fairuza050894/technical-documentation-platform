# ADR-022: Establish Generic Enterprise Document Generation with LLD First

- Status: Accepted
- Date: 2026-08-10
- Decision owners: Product Engineering and Technical Documentation

## Context

The platform now has four layers required before enterprise generation can be trusted:

1. a canonical Project document registry and checklist;
2. immutable Evidence Artifacts and classified Claims;
3. deterministic readiness and missing-information policies;
4. a Project Workbench that consumes those backend contracts without duplicating them.

The existing Technical Source Overview generator is deterministic and lifecycle-aware, but its
application service, renderer context, file naming, and `DocumentVersion.create` factory were
originally specialized for one system artifact.

Starting ten unrelated generators would duplicate lifecycle and factual-safety logic.

## Decision

1. Keep enterprise generation inside the Documents bounded context.
2. Introduce a generic enterprise generation profile contract and renderer/input ports.
3. Keep the Documents domain independent from Evidence, Readiness, Catalog, Projects, FastAPI, and
   SQLite.
4. Isolate cross-context Project, Workspace, Evidence, Readiness, Source, and Catalog adaptation in
   a Documents infrastructure adapter.
5. Use the canonical 0010C readiness result as the only generation eligibility gate.
6. Return canonical blocker/remediation details when generation is ineligible.
7. Start with `LLD` and profile key `enterprise-lld-v1`.
8. Select the latest governed Catalog snapshot deterministically as the initial LLD evidence basis.
9. Render normalized operations and schemas as observed technical facts with their source pointers.
10. Render `OBSERVED` and `INFERRED` LLD claims in separately labelled sections and preserve
    derivation references for inference.
11. Never render `UNVERIFIED` statements as factual document content.
12. Reuse the existing Document series, immutable version, checksum deduplication, workflow,
    download, and approval lifecycle.
13. Generalize `DocumentVersion.create` only by accepting an explicit document type; preserve
    Technical Source Overview as the default for backward compatibility.
14. Keep Markdown as the initial enterprise artifact format.
15. Introduce no new persistence tables or schema migration in this slice.
16. Keep AI outside factual generation and readiness decisions.

## Why not As-Built first

As-Built has a deliberately stronger readiness contract: a normalized technical snapshot plus a
direct `OBSERVED` As-Built claim. LLD can already reach blocker-free eligibility from the currently
implemented Catalog evidence while still exposing missing contextual claims as warnings.

Using LLD first proves the generic generation path without weakening the As-Built factual contract.

## Consequences

- Enterprise generation uses one reusable application pipeline rather than document-specific
  service methods.
- Existing Technical Source Overview clients remain compatible.
- LLD versions participate in the existing document checklist, lifecycle, download, review, and
  approval flows immediately.
- Readiness policy remains the single source of eligibility truth.
- Evidence/claim classification remains visible in the generated artifact.
- Later profiles can reuse the same pipeline while adding profile-specific input/rendering policy.
