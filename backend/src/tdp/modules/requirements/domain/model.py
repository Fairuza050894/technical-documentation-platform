import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from tdp.modules.requirements.domain.errors import (
    InvalidRequirementAcceptanceCriteriaError,
    InvalidRequirementIdError,
    InvalidRequirementKeyError,
    InvalidRequirementRationaleError,
    InvalidRequirementStatementError,
    InvalidRequirementStatusTransitionError,
    InvalidRequirementTitleError,
    InvalidTraceabilityTargetError,
)

_REQUIREMENT_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{1,39}$")


class RequirementType(StrEnum):
    BUSINESS = "BUSINESS"
    SYSTEM = "SYSTEM"
    FUNCTIONAL = "FUNCTIONAL"
    NON_FUNCTIONAL = "NON_FUNCTIONAL"
    COMPLIANCE = "COMPLIANCE"


class RequirementStatus(StrEnum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    RETIRED = "RETIRED"


class TraceabilityTargetType(StrEnum):
    FEATURE = "FEATURE"
    EVIDENCE = "EVIDENCE"
    DOCUMENT = "DOCUMENT"
    TEST = "TEST"
    CHANGE = "CHANGE"


class TraceabilityRelation(StrEnum):
    IMPLEMENTED_BY = "IMPLEMENTED_BY"
    SUPPORTED_BY = "SUPPORTED_BY"
    VERIFIED_BY = "VERIFIED_BY"
    DOCUMENTED_BY = "DOCUMENTED_BY"
    AFFECTED_BY = "AFFECTED_BY"


@dataclass(frozen=True, slots=True)
class RequirementId:
    value: UUID

    @classmethod
    def new(cls) -> "RequirementId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "RequirementId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidRequirementIdError("Requirement ID must be a valid UUID.") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class TraceabilityLinkId:
    value: UUID

    @classmethod
    def new(cls) -> "TraceabilityLinkId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "TraceabilityLinkId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidTraceabilityTargetError(
                "Traceability link ID must be a valid UUID."
            ) from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(slots=True)
class Requirement:
    id: RequirementId
    workspace_id: str
    project_id: str
    key: str
    requirement_type: RequirementType
    title: str
    statement: str
    acceptance_criteria: tuple[str, ...]
    rationale: str
    feature_id: str | None
    status: RequirementStatus
    revision: int
    created_by: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        workspace_id: str,
        project_id: str,
        key: str,
        requirement_type: RequirementType,
        title: str,
        statement: str,
        acceptance_criteria: tuple[str, ...],
        rationale: str,
        feature_id: str | None,
        created_by: str,
        now: datetime | None = None,
    ) -> "Requirement":
        timestamp = now or datetime.now(UTC)
        return cls(
            id=RequirementId.new(),
            workspace_id=_required_uuid(workspace_id, "Workspace reference"),
            project_id=_required_uuid(project_id, "Project reference"),
            key=_requirement_key(key),
            requirement_type=requirement_type,
            title=_title(title),
            statement=_statement(statement),
            acceptance_criteria=_criteria(acceptance_criteria),
            rationale=_rationale(rationale),
            feature_id=_optional_uuid(feature_id, "Feature reference"),
            status=RequirementStatus.DRAFT,
            revision=1,
            created_by=_actor(created_by),
            created_at=timestamp,
            updated_at=timestamp,
        )

    def revise(
        self,
        *,
        title: str,
        statement: str,
        acceptance_criteria: tuple[str, ...],
        rationale: str,
        feature_id: str | None,
        now: datetime | None = None,
    ) -> None:
        if self.status is RequirementStatus.RETIRED:
            raise InvalidRequirementStatusTransitionError(
                "A retired requirement cannot be revised."
            )
        self.title = _title(title)
        self.statement = _statement(statement)
        self.acceptance_criteria = _criteria(acceptance_criteria)
        self.rationale = _rationale(rationale)
        self.feature_id = _optional_uuid(feature_id, "Feature reference")
        self.status = RequirementStatus.DRAFT
        self.revision += 1
        self.updated_at = now or datetime.now(UTC)

    def approve(self, *, now: datetime | None = None) -> None:
        if self.status is not RequirementStatus.DRAFT:
            raise InvalidRequirementStatusTransitionError(
                "Only draft requirements can be approved."
            )
        self.status = RequirementStatus.APPROVED
        self.updated_at = now or datetime.now(UTC)

    def retire(self, *, now: datetime | None = None) -> None:
        if self.status is RequirementStatus.RETIRED:
            raise InvalidRequirementStatusTransitionError(
                "Requirement is already retired."
            )
        self.status = RequirementStatus.RETIRED
        self.updated_at = now or datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class RequirementRevision:
    requirement_id: RequirementId
    revision: int
    title: str
    statement: str
    acceptance_criteria: tuple[str, ...]
    rationale: str
    feature_id: str | None
    status: RequirementStatus
    actor: str
    recorded_at: datetime

    @classmethod
    def from_requirement(
        cls,
        requirement: Requirement,
        *,
        actor: str,
        now: datetime | None = None,
    ) -> "RequirementRevision":
        return cls(
            requirement_id=requirement.id,
            revision=requirement.revision,
            title=requirement.title,
            statement=requirement.statement,
            acceptance_criteria=requirement.acceptance_criteria,
            rationale=requirement.rationale,
            feature_id=requirement.feature_id,
            status=requirement.status,
            actor=_actor(actor),
            recorded_at=now or requirement.updated_at,
        )


@dataclass(frozen=True, slots=True)
class TraceabilityLink:
    id: TraceabilityLinkId
    requirement_id: RequirementId
    target_type: TraceabilityTargetType
    target_id: str
    relation: TraceabilityRelation
    created_by: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        requirement_id: RequirementId,
        target_type: TraceabilityTargetType,
        target_id: str,
        relation: TraceabilityRelation,
        created_by: str,
        now: datetime | None = None,
    ) -> "TraceabilityLink":
        normalized_target = target_id.strip()
        if not normalized_target or len(normalized_target) > 500:
            raise InvalidTraceabilityTargetError(
                "Traceability target must contain 1-500 characters."
            )
        return cls(
            id=TraceabilityLinkId.new(),
            requirement_id=requirement_id,
            target_type=target_type,
            target_id=normalized_target,
            relation=relation,
            created_by=_actor(created_by),
            created_at=now or datetime.now(UTC),
        )


def _requirement_key(value: str) -> str:
    normalized = value.strip().upper()
    if not _REQUIREMENT_KEY_PATTERN.fullmatch(normalized):
        raise InvalidRequirementKeyError(
            "Requirement key must contain 2-40 uppercase letters, numbers, or hyphens."
        )
    return normalized


def _title(value: str) -> str:
    normalized = " ".join(value.split())
    if not 3 <= len(normalized) <= 160:
        raise InvalidRequirementTitleError(
            "Requirement title must contain 3-160 characters."
        )
    return normalized


def _statement(value: str) -> str:
    normalized = " ".join(value.split())
    if not 10 <= len(normalized) <= 4000:
        raise InvalidRequirementStatementError(
            "Requirement statement must contain 10-4000 characters."
        )
    return normalized


def _criteria(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(" ".join(value.split()) for value in values if value.strip()))
    if not normalized:
        raise InvalidRequirementAcceptanceCriteriaError(
            "At least one acceptance criterion is required."
        )
    if len(normalized) > 25 or any(len(value) > 1000 for value in normalized):
        raise InvalidRequirementAcceptanceCriteriaError(
            "Acceptance criteria allow up to 25 entries of at most 1000 characters each."
        )
    return normalized


def _rationale(value: str) -> str:
    normalized = value.strip()
    if len(normalized) > 2000:
        raise InvalidRequirementRationaleError(
            "Requirement rationale must not exceed 2000 characters."
        )
    return normalized


def _actor(value: str) -> str:
    normalized = " ".join(value.split())
    if not 2 <= len(normalized) <= 300:
        raise InvalidTraceabilityTargetError("Actor identity must contain 2-300 characters.")
    return normalized


def _required_uuid(value: str, label: str) -> str:
    try:
        parsed = UUID(value)
    except ValueError as exc:
        raise InvalidTraceabilityTargetError(f"{label} must be a valid UUID.") from exc
    return str(parsed)


def _optional_uuid(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    return _required_uuid(value, label)
