import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from tdp.modules.requirements.domain.errors import (
    InvalidAcceptanceCriterionError,
    InvalidRequirementActorError,
    InvalidRequirementIdError,
    InvalidRequirementKeyError,
    InvalidRequirementOwnerError,
    InvalidRequirementRevisionIdError,
    InvalidRequirementStatementError,
    InvalidRequirementTitleError,
    InvalidTraceRelationError,
    InvalidTraceTargetError,
    RequirementRetiredError,
)

_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*$")


class RequirementType(StrEnum):
    BUSINESS = "BUSINESS"
    SYSTEM = "SYSTEM"
    NON_FUNCTIONAL = "NON_FUNCTIONAL"
    ACCEPTANCE = "ACCEPTANCE"


class RequirementStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class TraceTargetType(StrEnum):
    FEATURE = "FEATURE"
    EVIDENCE = "EVIDENCE"
    DOCUMENT = "DOCUMENT"


class TraceRelation(StrEnum):
    IMPLEMENTED_BY = "IMPLEMENTED_BY"
    VERIFIED_BY = "VERIFIED_BY"
    DOCUMENTED_BY = "DOCUMENTED_BY"


_ALLOWED_RELATIONS: dict[TraceTargetType, TraceRelation] = {
    TraceTargetType.FEATURE: TraceRelation.IMPLEMENTED_BY,
    TraceTargetType.EVIDENCE: TraceRelation.VERIFIED_BY,
    TraceTargetType.DOCUMENT: TraceRelation.DOCUMENTED_BY,
}


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
class RequirementRevisionId:
    value: UUID

    @classmethod
    def new(cls) -> "RequirementRevisionId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "RequirementRevisionId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidRequirementRevisionIdError(
                "Requirement revision ID must be a valid UUID."
            ) from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class RequirementKey:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not 2 <= len(normalized) <= 40 or _KEY_PATTERN.fullmatch(normalized) is None:
            raise InvalidRequirementKeyError(
                "Requirement key must contain 2-40 uppercase letters, numbers, or hyphen groups."
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class RequirementRevision:
    revision_id: RequirementRevisionId
    requirement_id: RequirementId
    project_id: str
    key: RequirementKey
    revision: int
    requirement_type: RequirementType
    status: RequirementStatus
    title: str
    statement: str
    owner: str
    feature_id: str | None
    acceptance_criteria: tuple[str, ...]
    changed_by: str
    change_reason: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        key: str,
        requirement_type: RequirementType,
        title: str,
        statement: str,
        owner: str,
        changed_by: str,
        change_reason: str,
        feature_id: str | None = None,
        acceptance_criteria: tuple[str, ...] = (),
        now: datetime | None = None,
    ) -> "RequirementRevision":
        return cls(
            revision_id=RequirementRevisionId.new(),
            requirement_id=RequirementId.new(),
            project_id=_required_text(project_id, "Project reference", 100),
            key=RequirementKey(key),
            revision=1,
            requirement_type=requirement_type,
            status=RequirementStatus.ACTIVE,
            title=_title(title),
            statement=_statement(statement),
            owner=_owner(owner),
            feature_id=_optional_reference(feature_id, "Feature reference"),
            acceptance_criteria=_criteria(acceptance_criteria),
            changed_by=_actor(changed_by),
            change_reason=_required_text(change_reason, "Change reason", 500),
            created_at=now or datetime.now(UTC),
        )

    def revise(
        self,
        *,
        title: str,
        statement: str,
        owner: str,
        changed_by: str,
        change_reason: str,
        requirement_type: RequirementType | None = None,
        feature_id: str | None = None,
        acceptance_criteria: tuple[str, ...] = (),
        now: datetime | None = None,
    ) -> "RequirementRevision":
        if self.status is RequirementStatus.RETIRED:
            raise RequirementRetiredError("A retired requirement cannot be revised.")
        return RequirementRevision(
            revision_id=RequirementRevisionId.new(),
            requirement_id=self.requirement_id,
            project_id=self.project_id,
            key=self.key,
            revision=self.revision + 1,
            requirement_type=requirement_type or self.requirement_type,
            status=RequirementStatus.ACTIVE,
            title=_title(title),
            statement=_statement(statement),
            owner=_owner(owner),
            feature_id=_optional_reference(feature_id, "Feature reference"),
            acceptance_criteria=_criteria(acceptance_criteria),
            changed_by=_actor(changed_by),
            change_reason=_required_text(change_reason, "Change reason", 500),
            created_at=now or datetime.now(UTC),
        )

    def retire(
        self,
        *,
        changed_by: str,
        change_reason: str,
        now: datetime | None = None,
    ) -> "RequirementRevision":
        if self.status is RequirementStatus.RETIRED:
            raise RequirementRetiredError("Requirement is already retired.")
        return RequirementRevision(
            revision_id=RequirementRevisionId.new(),
            requirement_id=self.requirement_id,
            project_id=self.project_id,
            key=self.key,
            revision=self.revision + 1,
            requirement_type=self.requirement_type,
            status=RequirementStatus.RETIRED,
            title=self.title,
            statement=self.statement,
            owner=self.owner,
            feature_id=self.feature_id,
            acceptance_criteria=self.acceptance_criteria,
            changed_by=_actor(changed_by),
            change_reason=_required_text(change_reason, "Change reason", 500),
            created_at=now or datetime.now(UTC),
        )


@dataclass(frozen=True, slots=True)
class TraceLink:
    id: UUID
    project_id: str
    requirement_revision_id: RequirementRevisionId
    target_type: TraceTargetType
    relation: TraceRelation
    target_reference: str
    verified: bool
    created_by: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        requirement_revision_id: RequirementRevisionId,
        target_type: TraceTargetType,
        relation: TraceRelation,
        target_reference: str,
        verified: bool,
        created_by: str,
        now: datetime | None = None,
    ) -> "TraceLink":
        expected = _ALLOWED_RELATIONS[target_type]
        if relation is not expected:
            raise InvalidTraceRelationError(
                f"{target_type.value} trace targets require relation {expected.value}."
            )
        reference = _required_text(target_reference, "Trace target reference", 200)
        return cls(
            id=uuid4(),
            project_id=_required_text(project_id, "Project reference", 100),
            requirement_revision_id=requirement_revision_id,
            target_type=target_type,
            relation=relation,
            target_reference=reference,
            verified=verified,
            created_by=_actor(created_by),
            created_at=now or datetime.now(UTC),
        )


def _title(value: str) -> str:
    normalized = " ".join(value.split())
    if not 3 <= len(normalized) <= 160:
        raise InvalidRequirementTitleError("Requirement title must contain 3-160 characters.")
    return normalized


def _statement(value: str) -> str:
    normalized = " ".join(value.split())
    if not 10 <= len(normalized) <= 4000:
        raise InvalidRequirementStatementError(
            "Requirement statement must contain 10-4000 characters."
        )
    return normalized


def _owner(value: str) -> str:
    normalized = " ".join(value.split())
    if not 2 <= len(normalized) <= 120:
        raise InvalidRequirementOwnerError("Requirement owner must contain 2-120 characters.")
    return normalized


def _actor(value: str) -> str:
    normalized = " ".join(value.split())
    if not 2 <= len(normalized) <= 160:
        raise InvalidRequirementActorError("Requirement actor must contain 2-160 characters.")
    return normalized


def _criteria(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        item = " ".join(value.split())
        if not 5 <= len(item) <= 1000:
            raise InvalidAcceptanceCriterionError(
                "Each acceptance criterion must contain 5-1000 characters."
            )
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _required_text(value: str, label: str, max_length: int) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > max_length:
        raise InvalidTraceTargetError(f"{label} must contain 1-{max_length} characters.")
    return normalized


def _optional_reference(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized or len(normalized) > 100:
        raise InvalidTraceTargetError(f"{label} must contain 1-100 characters.")
    return normalized
