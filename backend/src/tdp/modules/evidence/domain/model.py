import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from tdp.modules.evidence.domain.errors import (
    InvalidClaimDerivationError,
    InvalidClaimEvidenceError,
    InvalidClaimIdError,
    InvalidClaimStatementError,
    InvalidEvidenceArtifactIdError,
    InvalidEvidenceCaptureTimeError,
    InvalidEvidenceChecksumError,
    InvalidEvidenceReferenceError,
)

_CHECKSUM_PATTERN = re.compile(r"^[a-f0-9]{64}$")


class EvidenceKind(StrEnum):
    SOURCE_ARTIFACT = "SOURCE_ARTIFACT"
    CATALOG_SNAPSHOT = "CATALOG_SNAPSHOT"
    USER_JOURNEY = "USER_JOURNEY"
    DEPLOYMENT_RUNTIME = "DEPLOYMENT_RUNTIME"
    UAT_RESULT = "UAT_RESULT"


REFERENCED_EVIDENCE_KINDS: tuple[EvidenceKind, ...] = (
    EvidenceKind.USER_JOURNEY,
    EvidenceKind.DEPLOYMENT_RUNTIME,
    EvidenceKind.UAT_RESULT,
)


class EvidenceSourceSystem(StrEnum):
    SOURCE_REGISTRY = "SOURCE_REGISTRY"
    API_CATALOG = "API_CATALOG"
    GOVERNED_REFERENCE = "GOVERNED_REFERENCE"


class EvidenceCollectionMethod(StrEnum):
    SOURCE_IMPORT = "SOURCE_IMPORT"
    DETERMINISTIC_NORMALIZATION = "DETERMINISTIC_NORMALIZATION"
    REFERENCE_REGISTRATION = "REFERENCE_REGISTRATION"


class ClaimClassification(StrEnum):
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True, slots=True)
class EvidenceArtifactId:
    value: UUID

    @classmethod
    def new(cls) -> "EvidenceArtifactId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "EvidenceArtifactId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidEvidenceArtifactIdError(
                "Evidence artifact ID must be a valid UUID."
            ) from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class ClaimId:
    value: UUID

    @classmethod
    def new(cls) -> "ClaimId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "ClaimId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidClaimIdError("Claim ID must be a valid UUID.") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class EvidenceChecksum:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not _CHECKSUM_PATTERN.fullmatch(normalized):
            raise InvalidEvidenceChecksumError(
                "Evidence checksum must be a SHA-256 hexadecimal value."
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EvidenceArtifact:
    id: EvidenceArtifactId
    workspace_id: str
    project_id: str
    feature_id: str | None
    kind: EvidenceKind
    source_system: EvidenceSourceSystem
    source_reference: str
    origin_id: str
    checksum: EvidenceChecksum
    content_reference: str
    collection_method: EvidenceCollectionMethod
    collected_by: str
    captured_at: datetime
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        workspace_id: str,
        project_id: str,
        kind: EvidenceKind,
        source_system: EvidenceSourceSystem,
        source_reference: str,
        origin_id: str,
        checksum: str,
        content_reference: str,
        collection_method: EvidenceCollectionMethod,
        collected_by: str,
        captured_at: datetime,
        feature_id: str | None = None,
        now: datetime | None = None,
    ) -> "EvidenceArtifact":
        if captured_at.tzinfo is None or captured_at.utcoffset() is None:
            raise InvalidEvidenceCaptureTimeError(
                "Evidence capture time must include an explicit timezone."
            )
        return cls(
            id=EvidenceArtifactId.new(),
            workspace_id=_required_text(workspace_id, "Workspace reference", 100),
            project_id=_required_text(project_id, "Project reference", 100),
            feature_id=_optional_text(feature_id, "Feature reference", 100),
            kind=kind,
            source_system=source_system,
            source_reference=_required_text(source_reference, "Source reference", 500),
            origin_id=_required_text(origin_id, "Evidence origin", 200),
            checksum=EvidenceChecksum(checksum),
            content_reference=_required_text(content_reference, "Content reference", 500),
            collection_method=collection_method,
            collected_by=_required_text(collected_by, "Collector identity", 300),
            captured_at=captured_at,
            created_at=now or datetime.now(UTC),
        )


@dataclass(frozen=True, slots=True)
class Claim:
    id: ClaimId
    workspace_id: str
    project_id: str
    feature_id: str | None
    statement: str
    classification: ClaimClassification
    evidence_ids: tuple[EvidenceArtifactId, ...]
    derivation_reference: str
    relevant_document_types: tuple[str, ...]
    asserted_by: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        workspace_id: str,
        project_id: str,
        statement: str,
        classification: ClaimClassification,
        evidence_ids: tuple[EvidenceArtifactId, ...],
        derivation_reference: str,
        relevant_document_types: tuple[str, ...],
        asserted_by: str,
        feature_id: str | None = None,
        now: datetime | None = None,
    ) -> "Claim":
        normalized_statement = " ".join(statement.split())
        if not 3 <= len(normalized_statement) <= 2000:
            raise InvalidClaimStatementError("Claim statement must contain 3-2000 characters.")

        unique_evidence = tuple(dict.fromkeys(evidence_ids))
        derivation = derivation_reference.strip()

        if classification is ClaimClassification.OBSERVED and not unique_evidence:
            raise InvalidClaimEvidenceError(
                "Observed claims require at least one supporting evidence artifact."
            )
        if classification is ClaimClassification.INFERRED:
            if not unique_evidence:
                raise InvalidClaimEvidenceError(
                    "Inferred claims require at least one supporting evidence artifact."
                )
            if not derivation:
                raise InvalidClaimDerivationError(
                    "Inferred claims require an explicit deterministic derivation reference."
                )
        elif derivation:
            raise InvalidClaimDerivationError(
                "A derivation reference is only valid for an inferred claim."
            )

        if len(derivation) > 500:
            raise InvalidClaimDerivationError(
                "Claim derivation reference must not exceed 500 characters."
            )

        return cls(
            id=ClaimId.new(),
            workspace_id=_required_text(workspace_id, "Workspace reference", 100),
            project_id=_required_text(project_id, "Project reference", 100),
            feature_id=_optional_text(feature_id, "Feature reference", 100),
            statement=normalized_statement,
            classification=classification,
            evidence_ids=unique_evidence,
            derivation_reference=derivation,
            relevant_document_types=tuple(dict.fromkeys(relevant_document_types)),
            asserted_by=_required_text(asserted_by, "Claim actor", 300),
            created_at=now or datetime.now(UTC),
        )


def _required_text(value: str, label: str, max_length: int) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > max_length:
        raise InvalidEvidenceReferenceError(f"{label} must contain 1-{max_length} characters.")
    return normalized


def _optional_text(value: str | None, label: str, max_length: int) -> str | None:
    if value is None:
        return None
    return _required_text(value, label, max_length)
