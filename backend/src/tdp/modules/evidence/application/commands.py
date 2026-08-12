from dataclasses import dataclass
from datetime import datetime

from tdp.identity.model import RequestPrincipal


@dataclass(frozen=True, slots=True)
class RegisterSourceEvidenceCommand:
    project_id: str
    source_id: str
    principal: RequestPrincipal


@dataclass(frozen=True, slots=True)
class RegisterSnapshotEvidenceCommand:
    project_id: str
    synchronization_id: str
    principal: RequestPrincipal


@dataclass(frozen=True, slots=True)
class RegisterReferencedEvidenceCommand:
    project_id: str
    kind: str
    source_reference: str
    origin_id: str
    checksum: str
    content_reference: str
    captured_at: datetime
    feature_id: str | None
    principal: RequestPrincipal


@dataclass(frozen=True, slots=True)
class CreateClaimCommand:
    project_id: str
    statement: str
    classification: str
    evidence_ids: tuple[str, ...]
    derivation_reference: str
    relevant_document_types: tuple[str, ...]
    feature_id: str | None
    principal: RequestPrincipal
