import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from tdp.modules.governance.domain.errors import (
    InvalidRequirementError,
    InvalidTraceLinkError,
    InvalidWorkflowTransitionError,
)

_REQUIREMENT_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{1,39}$")


class RequirementKind(StrEnum):
    BUSINESS = "BUSINESS"
    FUNCTIONAL = "FUNCTIONAL"
    NON_FUNCTIONAL = "NON_FUNCTIONAL"
    TECHNICAL = "TECHNICAL"


class RequirementStatus(StrEnum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    RETIRED = "RETIRED"


class TraceTargetType(StrEnum):
    FEATURE = "FEATURE"
    EVIDENCE = "EVIDENCE"
    DOCUMENT = "DOCUMENT"
    TEST = "TEST"
    CHANGE = "CHANGE"


class TraceRelation(StrEnum):
    IMPLEMENTED_BY = "IMPLEMENTED_BY"
    VERIFIED_BY = "VERIFIED_BY"
    DOCUMENTED_BY = "DOCUMENTED_BY"
    DERIVED_FROM = "DERIVED_FROM"
    AFFECTED_BY = "AFFECTED_BY"


class ImpactSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class WorkflowState(StrEnum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class WorkflowAction(StrEnum):
    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REOPEN = "REOPEN"
    CLOSE = "CLOSE"


@dataclass(frozen=True, slots=True)
class RequirementRevision:
    id: str
    workspace_id: str
    project_id: str
    key: str
    revision: int
    kind: RequirementKind
    title: str
    statement: str
    acceptance_criteria: tuple[str, ...]
    owner: str
    status: RequirementStatus
    previous_revision_id: str | None
    created_by: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        workspace_id: str,
        project_id: str,
        key: str,
        kind: RequirementKind,
        title: str,
        statement: str,
        acceptance_criteria: tuple[str, ...],
        owner: str,
        created_by: str,
        revision: int = 1,
        previous_revision_id: str | None = None,
        status: RequirementStatus = RequirementStatus.DRAFT,
        now: datetime | None = None,
    ) -> "RequirementRevision":
        normalized_key = key.strip().upper()
        normalized_title = " ".join(title.split())
        normalized_statement = " ".join(statement.split())
        normalized_owner = " ".join(owner.split())
        normalized_actor = " ".join(created_by.split())
        criteria = tuple(" ".join(item.split()) for item in acceptance_criteria if item.strip())

        if not _REQUIREMENT_KEY_PATTERN.fullmatch(normalized_key):
            raise InvalidRequirementError(
                "Requirement key must contain 2-40 uppercase letters, numbers, or hyphens."
            )
        if not 3 <= len(normalized_title) <= 160:
            raise InvalidRequirementError("Requirement title must contain 3-160 characters.")
        if not 10 <= len(normalized_statement) <= 4000:
            raise InvalidRequirementError("Requirement statement must contain 10-4000 characters.")
        if not normalized_owner or len(normalized_owner) > 160:
            raise InvalidRequirementError("Requirement owner must contain 1-160 characters.")
        if not normalized_actor or len(normalized_actor) > 300:
            raise InvalidRequirementError("Requirement actor must contain 1-300 characters.")
        if revision < 1:
            raise InvalidRequirementError("Requirement revision must be at least 1.")
        if len(criteria) > 50 or any(len(item) > 1000 for item in criteria):
            raise InvalidRequirementError(
                "Acceptance criteria must contain at most 50 items of at most 1000 characters each."
            )

        _require_uuid(workspace_id, "Workspace reference")
        _require_uuid(project_id, "Project reference")
        if previous_revision_id is not None:
            _require_uuid(previous_revision_id, "Previous requirement revision")

        return cls(
            id=str(uuid4()),
            workspace_id=workspace_id,
            project_id=project_id,
            key=normalized_key,
            revision=revision,
            kind=kind,
            title=normalized_title,
            statement=normalized_statement,
            acceptance_criteria=criteria,
            owner=normalized_owner,
            status=status,
            previous_revision_id=previous_revision_id,
            created_by=normalized_actor,
            created_at=now or datetime.now(UTC),
        )


@dataclass(frozen=True, slots=True)
class TraceLink:
    id: str
    workspace_id: str
    project_id: str
    requirement_revision_id: str
    target_type: TraceTargetType
    target_id: str
    relation: TraceRelation
    rationale: str
    created_by: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        workspace_id: str,
        project_id: str,
        requirement_revision_id: str,
        target_type: TraceTargetType,
        target_id: str,
        relation: TraceRelation,
        rationale: str,
        created_by: str,
        now: datetime | None = None,
    ) -> "TraceLink":
        _require_uuid(workspace_id, "Workspace reference")
        _require_uuid(project_id, "Project reference")
        _require_uuid(requirement_revision_id, "Requirement revision reference")
        normalized_target = target_id.strip()
        normalized_rationale = " ".join(rationale.split())
        normalized_actor = " ".join(created_by.split())
        if not normalized_target or len(normalized_target) > 500:
            raise InvalidTraceLinkError("Trace target must contain 1-500 characters.")
        if len(normalized_rationale) > 1000:
            raise InvalidTraceLinkError("Trace rationale must not exceed 1000 characters.")
        if not normalized_actor or len(normalized_actor) > 300:
            raise InvalidTraceLinkError("Trace actor must contain 1-300 characters.")
        return cls(
            id=str(uuid4()),
            workspace_id=workspace_id,
            project_id=project_id,
            requirement_revision_id=requirement_revision_id,
            target_type=target_type,
            target_id=normalized_target,
            relation=relation,
            rationale=normalized_rationale,
            created_by=normalized_actor,
            created_at=now or datetime.now(UTC),
        )


@dataclass(frozen=True, slots=True)
class ImpactAssessment:
    id: str
    workspace_id: str
    project_id: str
    change_reference: str
    changed_target_type: TraceTargetType
    changed_target_id: str
    severity: ImpactSeverity
    impacted_requirement_ids: tuple[str, ...]
    required_actions: tuple[str, ...]
    workflow_state: WorkflowState
    rationale: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def evaluate(
        cls,
        *,
        workspace_id: str,
        project_id: str,
        change_reference: str,
        changed_target_type: TraceTargetType,
        changed_target_id: str,
        trace_links: tuple[TraceLink, ...],
        created_by: str,
        now: datetime | None = None,
    ) -> "ImpactAssessment":
        _require_uuid(workspace_id, "Workspace reference")
        _require_uuid(project_id, "Project reference")
        change_ref = change_reference.strip()
        target_id = changed_target_id.strip()
        actor = " ".join(created_by.split())
        if not change_ref or len(change_ref) > 500:
            raise InvalidRequirementError("Change reference must contain 1-500 characters.")
        if not target_id or len(target_id) > 500:
            raise InvalidRequirementError("Changed target must contain 1-500 characters.")
        if not actor:
            raise InvalidRequirementError("Impact actor is required.")

        impacted = tuple(dict.fromkeys(link.requirement_revision_id for link in trace_links))
        actions: list[str] = ["REVIEW_REQUIREMENT"]
        relations = {link.relation for link in trace_links}
        target_types = {link.target_type for link in trace_links}
        if TraceRelation.DOCUMENTED_BY in relations or TraceTargetType.DOCUMENT in target_types:
            actions.append("UPDATE_DOCUMENTATION")
        if TraceRelation.VERIFIED_BY in relations or TraceTargetType.TEST in target_types:
            actions.append("RUN_VERIFICATION")
        if TraceRelation.IMPLEMENTED_BY in relations or TraceTargetType.FEATURE in target_types:
            actions.append("REVIEW_IMPLEMENTATION")

        impacted_count = len(impacted)
        if impacted_count >= 5:
            severity = ImpactSeverity.CRITICAL
        elif impacted_count >= 2:
            severity = ImpactSeverity.HIGH
        elif impacted_count == 1:
            severity = ImpactSeverity.MEDIUM
        else:
            severity = ImpactSeverity.LOW
            actions = ["TRIAGE_UNMAPPED_CHANGE"]

        timestamp = now or datetime.now(UTC)
        rationale = (
            f"Deterministic trace policy evaluated {len(trace_links)} link(s) and "
            f"identified {impacted_count} impacted requirement revision(s)."
        )
        return cls(
            id=str(uuid4()),
            workspace_id=workspace_id,
            project_id=project_id,
            change_reference=change_ref,
            changed_target_type=changed_target_type,
            changed_target_id=target_id,
            severity=severity,
            impacted_requirement_ids=impacted,
            required_actions=tuple(dict.fromkeys(actions)),
            workflow_state=WorkflowState.OPEN,
            rationale=rationale,
            created_by=actor,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def transition(
        self,
        action: WorkflowAction,
        *,
        now: datetime | None = None,
    ) -> "ImpactAssessment":
        allowed: dict[tuple[WorkflowState, WorkflowAction], WorkflowState] = {
            (WorkflowState.OPEN, WorkflowAction.SUBMIT): WorkflowState.IN_REVIEW,
            (WorkflowState.IN_REVIEW, WorkflowAction.APPROVE): WorkflowState.APPROVED,
            (WorkflowState.IN_REVIEW, WorkflowAction.REJECT): WorkflowState.REJECTED,
            (WorkflowState.REJECTED, WorkflowAction.REOPEN): WorkflowState.OPEN,
            (WorkflowState.APPROVED, WorkflowAction.CLOSE): WorkflowState.CLOSED,
        }
        next_state = allowed.get((self.workflow_state, action))
        if next_state is None:
            raise InvalidWorkflowTransitionError(
                f"Action {action.value} is not valid from state {self.workflow_state.value}."
            )
        return ImpactAssessment(
            id=self.id,
            workspace_id=self.workspace_id,
            project_id=self.project_id,
            change_reference=self.change_reference,
            changed_target_type=self.changed_target_type,
            changed_target_id=self.changed_target_id,
            severity=self.severity,
            impacted_requirement_ids=self.impacted_requirement_ids,
            required_actions=self.required_actions,
            workflow_state=next_state,
            rationale=self.rationale,
            created_by=self.created_by,
            created_at=self.created_at,
            updated_at=now or datetime.now(UTC),
        )


@dataclass(frozen=True, slots=True)
class WorkflowEvent:
    id: str
    assessment_id: str
    action: WorkflowAction
    previous_state: WorkflowState
    new_state: WorkflowState
    actor: str
    comment: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        assessment_id: str,
        action: WorkflowAction,
        previous_state: WorkflowState,
        new_state: WorkflowState,
        actor: str,
        comment: str,
        now: datetime | None = None,
    ) -> "WorkflowEvent":
        _require_uuid(assessment_id, "Impact assessment reference")
        normalized_actor = " ".join(actor.split())
        normalized_comment = comment.strip()
        if not normalized_actor or len(normalized_actor) > 300:
            raise InvalidWorkflowTransitionError("Workflow actor must contain 1-300 characters.")
        if len(normalized_comment) > 2000:
            raise InvalidWorkflowTransitionError("Workflow comment must not exceed 2000 characters.")
        return cls(
            id=str(uuid4()),
            assessment_id=assessment_id,
            action=action,
            previous_state=previous_state,
            new_state=new_state,
            actor=normalized_actor,
            comment=normalized_comment,
            created_at=now or datetime.now(UTC),
        )


def _require_uuid(value: str, label: str) -> None:
    try:
        UUID(value)
    except ValueError as exc:
        raise InvalidRequirementError(f"{label} must be a valid UUID.") from exc
