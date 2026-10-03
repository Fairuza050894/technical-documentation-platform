from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4

from tdp.modules.workflow.domain.errors import (
    InvalidWorkflowAssigneeError,
    InvalidWorkflowCommentError,
    InvalidWorkflowEntityError,
    InvalidWorkflowItemIdError,
    InvalidWorkflowTitleError,
    InvalidWorkflowTransitionError,
)


class WorkflowEntityType(StrEnum):
    REQUIREMENT = "REQUIREMENT"
    DOCUMENT = "DOCUMENT"
    CHANGE_IMPACT = "CHANGE_IMPACT"


class WorkflowPriority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class WorkflowState(StrEnum):
    OPEN = "OPEN"
    TRIAGED = "TRIAGED"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class WorkflowAction(StrEnum):
    TRIAGE = "TRIAGE"
    START = "START"
    REQUEST_REVIEW = "REQUEST_REVIEW"
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    CLOSE = "CLOSE"
    CANCEL = "CANCEL"
    REOPEN = "REOPEN"


_TRANSITIONS: dict[tuple[WorkflowState, WorkflowAction], WorkflowState] = {
    (WorkflowState.OPEN, WorkflowAction.TRIAGE): WorkflowState.TRIAGED,
    (WorkflowState.OPEN, WorkflowAction.CANCEL): WorkflowState.CANCELLED,
    (WorkflowState.TRIAGED, WorkflowAction.START): WorkflowState.IN_PROGRESS,
    (WorkflowState.TRIAGED, WorkflowAction.CANCEL): WorkflowState.CANCELLED,
    (WorkflowState.IN_PROGRESS, WorkflowAction.REQUEST_REVIEW): WorkflowState.IN_REVIEW,
    (WorkflowState.IN_PROGRESS, WorkflowAction.CANCEL): WorkflowState.CANCELLED,
    (WorkflowState.IN_REVIEW, WorkflowAction.APPROVE): WorkflowState.APPROVED,
    (WorkflowState.IN_REVIEW, WorkflowAction.REQUEST_CHANGES): WorkflowState.IN_PROGRESS,
    (WorkflowState.APPROVED, WorkflowAction.CLOSE): WorkflowState.CLOSED,
    (WorkflowState.APPROVED, WorkflowAction.REOPEN): WorkflowState.IN_PROGRESS,
    (WorkflowState.CLOSED, WorkflowAction.REOPEN): WorkflowState.IN_PROGRESS,
    (WorkflowState.CANCELLED, WorkflowAction.REOPEN): WorkflowState.OPEN,
}

_SLA_HOURS: dict[WorkflowPriority, int] = {
    WorkflowPriority.P0: 4,
    WorkflowPriority.P1: 24,
    WorkflowPriority.P2: 72,
    WorkflowPriority.P3: 168,
}


@dataclass(frozen=True, slots=True)
class WorkflowItemId:
    value: UUID

    @classmethod
    def new(cls) -> "WorkflowItemId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "WorkflowItemId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidWorkflowItemIdError(
                "Workflow item ID must be a valid UUID."
            ) from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class WorkflowEventId:
    value: UUID

    @classmethod
    def new(cls) -> "WorkflowEventId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "WorkflowEventId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidWorkflowItemIdError(
                "Workflow event ID must be a valid UUID."
            ) from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(slots=True)
class WorkflowItem:
    id: WorkflowItemId
    workspace_id: str
    project_id: str
    entity_type: WorkflowEntityType
    entity_id: str
    title: str
    priority: WorkflowPriority
    state: WorkflowState
    assignee: str
    created_by: str
    due_at: datetime
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        workspace_id: str,
        project_id: str,
        entity_type: WorkflowEntityType,
        entity_id: str,
        title: str,
        priority: WorkflowPriority,
        assignee: str,
        created_by: str,
        now: datetime | None = None,
    ) -> "WorkflowItem":
        timestamp = now or datetime.now(UTC)
        normalized_entity = entity_id.strip()
        if not normalized_entity or len(normalized_entity) > 500:
            raise InvalidWorkflowEntityError(
                "Workflow entity reference must contain 1-500 characters."
            )
        normalized_title = " ".join(title.split())
        if not 3 <= len(normalized_title) <= 240:
            raise InvalidWorkflowTitleError(
                "Workflow title must contain 3-240 characters."
            )
        normalized_assignee = _assignee(assignee)
        normalized_actor = _actor(created_by)
        return cls(
            id=WorkflowItemId.new(),
            workspace_id=_uuid(workspace_id, "Workspace reference"),
            project_id=_uuid(project_id, "Project reference"),
            entity_type=entity_type,
            entity_id=normalized_entity,
            title=normalized_title,
            priority=priority,
            state=WorkflowState.OPEN,
            assignee=normalized_assignee,
            created_by=normalized_actor,
            due_at=timestamp + timedelta(hours=_SLA_HOURS[priority]),
            created_at=timestamp,
            updated_at=timestamp,
        )

    def transition(
        self,
        action: WorkflowAction,
        *,
        now: datetime | None = None,
    ) -> tuple[WorkflowState, WorkflowState]:
        previous = self.state
        target = _TRANSITIONS.get((previous, action))
        if target is None:
            raise InvalidWorkflowTransitionError(
                f"Action {action.value} is not allowed from state {previous.value}."
            )
        self.state = target
        self.updated_at = now or datetime.now(UTC)
        return previous, target


@dataclass(frozen=True, slots=True)
class WorkflowEvent:
    id: WorkflowEventId
    workflow_item_id: WorkflowItemId
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
        workflow_item_id: WorkflowItemId,
        action: WorkflowAction,
        previous_state: WorkflowState,
        new_state: WorkflowState,
        actor: str,
        comment: str,
        now: datetime | None = None,
    ) -> "WorkflowEvent":
        normalized_comment = comment.strip()
        if len(normalized_comment) > 2000:
            raise InvalidWorkflowCommentError(
                "Workflow comment must not exceed 2000 characters."
            )
        return cls(
            id=WorkflowEventId.new(),
            workflow_item_id=workflow_item_id,
            action=action,
            previous_state=previous_state,
            new_state=new_state,
            actor=_actor(actor),
            comment=normalized_comment,
            created_at=now or datetime.now(UTC),
        )


def _uuid(value: str, label: str) -> str:
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise InvalidWorkflowEntityError(f"{label} must be a valid UUID.") from exc


def _actor(value: str) -> str:
    normalized = " ".join(value.split())
    if not 2 <= len(normalized) <= 300:
        raise InvalidWorkflowEntityError("Actor identity must contain 2-300 characters.")
    return normalized


def _assignee(value: str) -> str:
    normalized = " ".join(value.split())
    if len(normalized) > 160:
        raise InvalidWorkflowAssigneeError(
            "Workflow assignee must not exceed 160 characters."
        )
    return normalized
