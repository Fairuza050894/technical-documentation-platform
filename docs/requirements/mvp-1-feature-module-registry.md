# MVP 1 — Feature / Module Registry and Documentation Map

## Objective

Introduce the stable capability boundary between Project and Documentation without rewriting
existing project-scoped technical evidence or document version history.

## Domain hierarchy

```text
Workspace
└── Project
    └── Feature / Module
        └── Documentation Map
            └── Document (future feature link)
                └── Document Version
```

## Functional requirements

1. A feature or module belongs to exactly one Project.
2. Its key is unique within that Project and remains stable across future changes.
3. Supported kinds are `FEATURE` and `MODULE`.
4. Supported lifecycle states are `ACTIVE` and `ARCHIVED`.
5. Archived Projects and Workspaces are read-only for feature mutation.
6. Creating a capability applies the versioned policy `feature-documentation-baseline-v1`.
7. The baseline produces required and optional documentation-map entries deterministically.
8. Coverage is calculated as `MISSING`, `PLANNED`, or `AVAILABLE`; users do not select the
   result manually.
9. Existing project-scoped documents, snapshots, comparisons, and versions are not migrated or
   reassigned in this patch.
10. Feature context is persistent in the browser URL.

## Baseline policy v1

A Feature requires Business Requirement, Functional Specification, User Guide, and Test
Scenario. A Module requires System Requirements Specification, Functional Specification, API
Documentation, Database Specification, and Test Scenario. All other supported document types
are optional baseline coverage.

This policy is only the deterministic starting point. Requirement revision, Git/API evidence,
impact analysis, and version-decision rules will refine it in later patches.
