from datetime import UTC, datetime, timedelta

import pytest

from tdp.modules.workflow.domain.errors import InvalidWorkflowTransitionError
from tdp.modules.workflow.domain.model import (
    WorkflowAction,
    WorkflowEntityType,
    WorkflowItem,
    WorkflowPriority,
    WorkflowState,
)


def work_item() -> WorkflowItem:
    return WorkflowItem.create(
        workspace_id="11111111-1111-4111-8111-111111111111",
        project_id="22222222-2222-4222-8222-222222222222",
        entity_type=WorkflowEntityType.REQUIREMENT,
        entity_id="33333333-3333-4333-8333-333333333333",
        title="Review shipment requirement",
        priority=WorkflowPriority.P1,
        assignee="System Analyst",
        created_by="Technical Writer [local:writer]",
        now=datetime(2026, 10, 3, 8, 0, tzinfo=UTC),
    )


def test_workflow_enforces_state_machine_and_priority_sla() -> None:
    item = work_item()

    assert item.due_at == item.created_at + timedelta(hours=24)
    item.transition(WorkflowAction.TRIAGE)
    item.transition(WorkflowAction.START)
    item.transition(WorkflowAction.REQUEST_REVIEW)
    item.transition(WorkflowAction.APPROVE)
    item.transition(WorkflowAction.CLOSE)

    assert item.state is WorkflowState.CLOSED


def test_workflow_rejects_approval_before_review() -> None:
    item = work_item()

    with pytest.raises(InvalidWorkflowTransitionError):
        item.transition(WorkflowAction.APPROVE)
