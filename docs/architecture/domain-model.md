# Domain Model

| Field | Value |
|---|---|
| Document ID | TDP-ARC-004 |
| Status | Controlled draft |
| Owner | Architecture and Product |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Current hierarchy

```mermaid
classDiagram
class Workspace
class Project
class FeatureModule
class Source
class SynchronizationRun
class ApiCatalog
class Document
class DocumentVersion
class WorkflowEvent

Workspace "1" --> "*" Project
Project "1" --> "*" FeatureModule
Project "1" --> "*" Source
Source "1" --> "*" SynchronizationRun
SynchronizationRun "1" --> "1" ApiCatalog
Project "1" --> "*" Document
Document "1" --> "*" DocumentVersion
DocumentVersion "1" --> "*" WorkflowEvent
```

## Current invariants

- Workspace, Project, Feature, Source, Document, and Version identities are stable.
- Archived governance boundaries remain readable and block new mutations.
- Source artifacts are checksummed.
- Synchronization snapshots are immutable.
- identical normalized document content reuses an existing checksum-backed version.
- lifecycle transitions are domain-controlled.
- workflow actor snapshots come from a server-resolved principal.

## Feature documentation baseline

The Feature or Module Registry defines required and optional document types through a versioned baseline policy. Existing project-scoped documents are not automatically mapped to a feature because that relationship is not yet supported by evidence.

## Planned domain expansion

```mermaid
classDiagram
class Requirement
class RequirementRevision
class EvidenceSource
class EvidenceSnapshot
class ChangeSet
class ImpactDecision
class VersionPolicy
class DocumentProfile
class TemplateVersion
class Release

Requirement "1" --> "*" RequirementRevision
EvidenceSource "1" --> "*" EvidenceSnapshot
RequirementRevision "*" --> "*" EvidenceSnapshot
ChangeSet "*" --> "*" EvidenceSnapshot
ChangeSet "1" --> "*" ImpactDecision
VersionPolicy "1" --> "*" ImpactDecision
DocumentProfile "1" --> "*" TemplateVersion
ImpactDecision "*" --> "*" DocumentVersion
Release "*" --> "*" DocumentVersion
```

The planned model is descriptive only until implemented through requirements, ADRs, code, and tests.
