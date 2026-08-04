# Getting Started

| Field | Value |
|---|---|
| Document ID | TDP-UG-001 |
| Status | Controlled draft |
| Owner | Technical Documentation |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## 1. Open the application

Start the backend and frontend, then open `http://127.0.0.1:4173`.

## 2. Select a Workspace

The sidebar Workspace selector defines the active operational boundary. A Workspace may contain multiple Projects.

## 3. Create or open a Project

Use **Projects** to create a Project in the selected Workspace. Opening a Project enters its Workbench without replacing Workspace context.

## 4. Register Features or Modules

Open **Features** and create stable capability boundaries. Inspect the Documentation Map to see required, optional, missing, planned, and available document types.

## 5. Import an OpenAPI source

Open **Sources**, choose a valid OpenAPI 3.0 or 3.1 JSON or YAML file, and import it. The platform stores a checksum-backed local artifact.

## 6. Synchronize the API Catalog

Open **API Catalog** and synchronize the source. The platform creates a normalized immutable snapshot.

## 7. Compare changes

When two completed snapshots exist, use **Changes** to classify added, modified, removed, and breaking changes.

## 8. Generate a document

Open **Documents**, select the target snapshot and optional baseline, provide a revision reason, and generate a Technical Source Overview.

The acting identity is resolved by the server and cannot be typed by the user.

## 9. Review versions

Use version history to preview, download, compare, submit for review, request changes, approve, or supersede according to valid lifecycle transitions.

## Current limitation

Approval in local development is not enterprise authorization. OIDC, RBAC, and separation of duties are required before shared production use.
