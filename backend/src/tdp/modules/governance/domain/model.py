from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class RequirementType(StrEnum):
    BUSINESS = "BUSINESS"
    SYSTEM = "SYSTEM"
    NON_FUNCTIONAL = "NON_FUNCTIONAL"


class RequirementStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class TraceTargetType(StrEnum):
    FEATURE = "FEATURE"
    EVIDENCE = "EVIDENCE"
    TEST = "TEST"
    DOCUMENT = "DOCUMENT"
    RELEASE = "RELEASE"
    SOURCE = "SOURCE"


class ChangeSurface(StrEnum):
    API = "API"
    SCHEMA = "SCHEMA"
    REPOSITORY = "REPOSITORY"
    TEST = "TEST"
    DEPLOYMENT = "DEPLOYMENT"
    RUNTIME = "RUNTIME"


class ImpactTarget(StrEnum):
    DOCUMENTATION = "DOCUMENTATION"
    TESTING = "TESTING"
    ARCHITECTURE = "ARCHITECTURE"
    RELEASE = "RELEASE"
    SECURITY = "SECURITY"


class WorkflowState(StrEnum):
    OPEN = "OPEN"
    ANALYSIS = "ANALYSIS"
    UPDATE_REQUIRED = "UPDATE_REQUIRED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    RELEASED = "RELEASED"
    REJECTED = "REJECTED"


_ALLOWED_WORKFLOW_TRANSITIONS: dict[WorkflowState, frozenset[WorkflowState]] = {
    WorkflowState.OPEN: frozenset({WorkflowState.ANALYSIS, WorkflowState.REJECTED}),
    WorkflowState.ANALYSIS: frozenset(
        {WorkflowState.UPDATE_REQUIRED, WorkflowState.APPROVED, WorkflowState.REJECTED}
    ),
    WorkflowState.UPDATE_REQUIRED: frozenset(
        {WorkflowState.IN_REVIEW, WorkflowState.REJECTED}
    ),
    WorkflowState.IN_REVIEW: frozenset(
        {WorkflowState.APPROVED, WorkflowState.UPDATE_REQUIRED, WorkflowState.REJECTED}
    ),
    WorkflowState.APPROVED: frozenset({WorkflowState.RELEASED, WorkflowState.REJECTED}),
    WorkflowState.RELEASED: frozenset(),
    WorkflowState.REJECTED: frozenset({WorkflowState.ANALYSIS}),
}


_IMPACT_POLICY: dict[ChangeSurface, tuple[ImpactTarget, ...]] = {
    ChangeSurface.API: (
        ImpactTarget.DOCUMENTATION,
        ImpactTarget.TESTING,
        ImpactTarget.RELEASE,
    ),
    ChangeSurface.SCHEMA: (
        ImpactTarget.DOCUMENTATION,
        ImpactTarget.TESTING,
        ImpactTarget.ARCHITECTURE,
    ),
    ChangeSurface.REPOSITORY: (
        ImpactTarget.TESTING,
        ImpactTarget.ARCHITECTURE,
    ),
    ChangeSurface.TEST: (ImpactTarget.RELEASE,),
    ChangeSurface.DEPLOYMENT: (
        ImpactTarget.DOCUMENTATION,
        ImpactTarget.RELEASE,
        ImpactTarget.SECURITY,
    ),
    ChangeSurface.RUNTIME: (
        ImpactTarget.DOCUMENTATION,
        ImpactTarget.SECURITY,
    ),
}


def _required_text(value: str, label: str, max_length: int) -> str:
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > max_length:
        raise ValueError(f"{label} must contain 1-{max_length} characters.")
    return normalized


def _uuid(value: str, label: str) -> str:
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid UUID.") from exc


@dataclass(frozen=True, slots=True)
class RequirementRevision:
    id: str
    requirement_id: str
    project_id: str
    revision: int
    requirement_type: RequirementType
    status: RequirementStatus
    title: str
    statement: str
    rationale: str
    created_by: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        requirement_type: RequirementType,
        title: str,
        statement: str,
        rationale: str,
        created_by: str,
        requirement_id: str | None = None,
        revision: int = 1,
        status: RequirementStatus = RequirementStatus.ACTIVE,
        now: datetime | None = None,
    ) -> "RequirementRevision":
        if revision < 1:
            raise ValueError("Requirement revision must be at least 1.")
        stable_id = requirement_id or str(uuid4())
        return cls(
            id=str(uuid4()),
            requirement_id=_uuid(stable_id, "Requirement ID"),
            project_id=_uuid(project_id, "Project ID"),
            revision=revision,
            requirement_type=requirement_type,
            status=status,
            title=_required_text(title, "Requirement title", 160),
            statement=_required_text(statement, "Requirement statement", 2000),
            rationale=_required_text(rationale, "Requirement rationale", 1000),
            created_by=_required_text(created_by, "Requirement actor", 120),
            created_at=now or datetime.now(UTC),
        )


@dataclass(frozen=True, slots=True)
class TraceLink:
    id: str
    project_id: str
    requirement_id: str
    target_type: TraceTargetType
    target_id: str
    relation: str
    created_by: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        requirement_id: str,
        target_type: TraceTargetType,
        target_id: str,
        relation: str,
        created_by: str,
        now: datetime | None = None,
    ) -> "TraceLink":
        return cls(
            id=str(uuid4()),
            project_id=_uuid(project_id, "Project ID"),
            requirement_id=_uuid(requirement_id, "Requirement ID"),
            target_type=target_type,
            target_id=_required_text(target_id, "Trace target", 200),
            relation=_required_text(relation, "Trace relation", 80),
            created_by=_required_text(created_by, "Trace actor", 120),
            created_at=now or datetime.now(UTC),
        )


@dataclass(frozen=True, slots=True)
class ImpactAssessment:
    id: str
    project_id: str
    change_reference: str
    surface: ChangeSurface
    affected_targets: tuple[ImpactTarget, ...]
    requires_action: bool
    assessed_by: str
    assessed_at: datetime

    @classmethod
    def assess(
        cls,
        *,
        project_id: str,
        change_reference: str,
        surface: ChangeSurface,
        assessed_by: str,
        now: datetime | None = None,
    ) -> "ImpactAssessment":
        targets = _IMPACT_POLICY[surface]
        return cls(
            id=str(uuid4()),
            project_id=_uuid(project_id, "Project ID"),
            change_reference=_required_text(change_reference, "Change reference", 300),
            surface=surface,
            affected_targets=targets,
            requires_action=bool(targets),
            assessed_by=_required_text(assessed_by, "Impact actor", 120),
            assessed_at=now or datetime.now(UTC),
        )


@dataclass(frozen=True, slots=True)
class WorkflowCase:
    id: str
    project_id: str
    impact_assessment_id: str
    owner: str
    state: WorkflowState
    created_by: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        impact_assessment_id: str,
        owner: str,
        created_by: str,
        now: datetime | None = None,
    ) -> "WorkflowCase":
        timestamp = now or datetime.now(UTC)
        return cls(
            id=str(uuid4()),
            project_id=_uuid(project_id, "Project ID"),
            impact_assessment_id=_uuid(impact_assessment_id, "Impact assessment ID"),
            owner=_required_text(owner, "Workflow owner", 120),
            state=WorkflowState.OPEN,
            created_by=_required_text(created_by, "Workflow actor", 120),
            created_at=timestamp,
            updated_at=timestamp,
        )

    def transition(
        self,
        target: WorkflowState,
        *,
        now: datetime | None = None,
    ) -> "WorkflowCase":
        if target not in _ALLOWED_WORKFLOW_TRANSITIONS[self.state]:
            raise ValueError(
                f"Workflow transition {self.state.value} -> {target.value} is not allowed."
            )
        return WorkflowCase(
            id=self.id,
            project_id=self.project_id,
            impact_assessment_id=self.impact_assessment_id,
            owner=self.owner,
            state=target,
            created_by=self.created_by,
            created_at=self.created_at,
            updated_at=now or datetime.now(UTC),
        )


def impact_targets_for(surface: ChangeSurface) -> tuple[ImpactTarget, ...]:
    return _IMPACT_POLICY[surface]
