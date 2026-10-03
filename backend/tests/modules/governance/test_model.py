from datetime import UTC, datetime
from uuid import uuid4

import pytest

from tdp.modules.governance.domain.errors import InvalidWorkflowTransitionError
from tdp.modules.governance.domain.model import (
    ImpactAssessment,
    ImpactSeverity,
    RequirementKind,
    RequirementRevision,
    TraceLink,
    TraceRelation,
    TraceTargetType,
    WorkflowAction,
    WorkflowState,
)


def _uuid() -> str:
    return str(uuid4())


def _requirement() -> RequirementRevision:
    return RequirementRevision.create(
        workspace_id=_uuid(),
        project_id=_uuid(),
        key="REQ-001",
        kind=RequirementKind.FUNCTIONAL,
        title="Driver meal allowance",
        statement="The platform shall calculate the eligible driver meal allowance deterministically.",
        acceptance_criteria=("Allowance uses the approved policy version.",),
        owner="Product Owner",
        created_by="Technical Writer",
        now=datetime(2026, 10, 3, tzinfo=UTC),
    )


def test_requirement_revision_normalizes_governed_fields() -> None:
    requirement = _requirement()

    assert requirement.key == "REQ-001"
    assert requirement.revision == 1
    assert requirement.status.value == "DRAFT"
    assert requirement.acceptance_criteria == ("Allowance uses the approved policy version.",)


def test_impact_policy_marks_unmapped_change_for_triage() -> None:
    requirement = _requirement()

    assessment = ImpactAssessment.evaluate(
        workspace_id=requirement.workspace_id,
        project_id=requirement.project_id,
        change_reference="commit:abc123",
        changed_target_type=TraceTargetType.CHANGE,
        changed_target_id="abc123",
        trace_links=(),
        created_by="Engineer",
    )

    assert assessment.severity is ImpactSeverity.LOW
    assert assessment.impacted_requirement_ids == ()
    assert assessment.required_actions == ("TRIAGE_UNMAPPED_CHANGE",)
    assert assessment.workflow_state is WorkflowState.OPEN


def test_impact_policy_derives_actions_from_traceability() -> None:
    requirement = _requirement()
    document_link = TraceLink.create(
        workspace_id=requirement.workspace_id,
        project_id=requirement.project_id,
        requirement_revision_id=requirement.id,
        target_type=TraceTargetType.DOCUMENT,
        target_id="TSD-024",
        relation=TraceRelation.DOCUMENTED_BY,
        rationale="The TSD describes the requirement implementation.",
        created_by="Technical Writer",
    )

    assessment = ImpactAssessment.evaluate(
        workspace_id=requirement.workspace_id,
        project_id=requirement.project_id,
        change_reference="doc:TSD-024",
        changed_target_type=TraceTargetType.DOCUMENT,
        changed_target_id="TSD-024",
        trace_links=(document_link,),
        created_by="Technical Writer",
    )

    assert assessment.severity is ImpactSeverity.MEDIUM
    assert assessment.impacted_requirement_ids == (requirement.id,)
    assert "UPDATE_DOCUMENTATION" in assessment.required_actions


def test_workflow_requires_human_review_before_approval() -> None:
    requirement = _requirement()
    assessment = ImpactAssessment.evaluate(
        workspace_id=requirement.workspace_id,
        project_id=requirement.project_id,
        change_reference="commit:def456",
        changed_target_type=TraceTargetType.CHANGE,
        changed_target_id="def456",
        trace_links=(),
        created_by="Engineer",
    )

    with pytest.raises(InvalidWorkflowTransitionError):
        assessment.transition(WorkflowAction.APPROVE)

    submitted = assessment.transition(WorkflowAction.SUBMIT)
    approved = submitted.transition(WorkflowAction.APPROVE)

    assert submitted.workflow_state is WorkflowState.IN_REVIEW
    assert approved.workflow_state is WorkflowState.APPROVED
