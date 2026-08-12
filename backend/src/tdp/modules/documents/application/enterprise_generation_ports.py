from dataclasses import dataclass
from typing import Protocol

from tdp.modules.documents.domain.generation import (
    EnterpriseDocumentGenerationProfile,
    GenerationReadinessSnapshot,
)


@dataclass(frozen=True, slots=True)
class GenerationEvidenceFact:
    id: str
    kind: str
    checksum: str
    source_reference: str
    content_reference: str
    captured_at: str


@dataclass(frozen=True, slots=True)
class GenerationClaimFact:
    id: str
    classification: str
    statement: str
    evidence_ids: tuple[str, ...]
    derivation_reference: str


@dataclass(frozen=True, slots=True)
class GenerationOperationFact:
    method: str
    path: str
    operation_id: str
    summary: str
    description: str
    tags: tuple[str, ...]
    deprecated: bool
    security_schemes: tuple[str, ...]
    parameters: tuple[str, ...]
    request_body: str
    responses: tuple[str, ...]
    source_pointer: str


@dataclass(frozen=True, slots=True)
class GenerationSchemaFact:
    name: str
    schema_type: str
    description: str
    required_fields: tuple[str, ...]
    properties: tuple[str, ...]
    source_pointer: str


@dataclass(frozen=True, slots=True)
class EnterpriseGenerationContext:
    profile: EnterpriseDocumentGenerationProfile
    readiness: GenerationReadinessSnapshot
    project_id: str
    project_key: str
    project_name: str
    project_description: str
    workspace_id: str
    source_id: str
    source_name: str
    api_title: str
    api_version: str
    openapi_version: str
    target_run_id: str | None
    source_checksum: str
    snapshot_completed_at: str | None
    primary_evidence_id: str
    primary_evidence_kind: str
    available_snapshot_count: int
    evidence: tuple[GenerationEvidenceFact, ...]
    claims: tuple[GenerationClaimFact, ...]
    operations: tuple[GenerationOperationFact, ...]
    schemas: tuple[GenerationSchemaFact, ...]


class EnterpriseGenerationInputProvider(Protocol):
    async def readiness(
        self,
        project_id: str,
        profile: EnterpriseDocumentGenerationProfile,
    ) -> GenerationReadinessSnapshot: ...

    async def collect(
        self,
        project_id: str,
        profile: EnterpriseDocumentGenerationProfile,
    ) -> EnterpriseGenerationContext: ...


class EnterpriseDocumentRenderer(Protocol):
    def render(self, context: EnterpriseGenerationContext) -> str: ...
