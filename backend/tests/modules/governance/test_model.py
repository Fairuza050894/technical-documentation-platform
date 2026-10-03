from datetime import UTC, datetime
from uuid import uuid4

import pytest

from tdp.modules.governance.domain.model import (
    ChangeSurface,
    ImpactAssessment,
    ImpactTarget,
    RequirementRevision,
    RequirementType,
    WorkflowCase,
    WorkflowState,
)


def test_requirement_revision_preserves_stable_requirement_identity() -> None:
    project_id = str(uuid4())
    requirement_id = str(uuid4())
    first = RequirementRevision.create(
        project_id=project_id,
        requirement_id=requirement_id,
        revision=1,
        requirement_type=RequirementType.SYSTEM,
        title="Capture API evidence",
        statement="The platform shall capture immutable API evidence.",
        rationale="Documentation must remain traceable to source evidence.",
        created_by="Technical Writer [local:test]",
        now=datetime(2026, 10, 3, tzinfo=UTC),
    )
    second = RequirementRevision.create(
        project_id=project_id,
        requirement_id=requirement_id,
        revision=2,
        requirement_type=RequirementType.SYSTEM,
        title="Capture API evidence",
        statement="The platform shall capture immutable API and schema evidence.",
        rationale="Change impact requires stable evidence provenance.",
        created_by="Technical Writer [local:test]",
        now=datetime(2026, 10, 3, tzinfo=UTC),
    )

    assert first.requirement_id == second.requirement_id == requirement_id
    assert first.id != second.id
    assert second.revision == 2


def test_api_change_policy_is_deterministic() -> None:
    assessment = ImpactAssessment.assess(
        project_id=str(uuid4()),
        change_reference="catalog-change:123",
        surface=ChangeSurface.API,
        assessed_by="System [local:test]",
        now=datetime(2026, 10, 3, tzinfo=UTC),
    )

    assert assessment.affected_targets == (
        ImpactTarget.DOCUMENTATION,
        ImpactTarget.TESTING,
        ImpactTarget.RELEASE,
    )
    assert assessment.requires_action is True


def test_workflow_rejects_transition_that_skips_governance_gate() -> None:
    case = WorkflowCase.create(
        project_id=str(uuid4()),
        impact_assessment_id=str(uuid4()),
        owner="Technical Writer",
        created_by="System [local:test]",
        now=datetime(2026, 10, 3, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="not allowed"):
        case.transition(WorkflowState.RELEASED)

    analysis = case.transition(WorkflowState.ANALYSIS)
    update_required = analysis.transition(WorkflowState.UPDATE_REQUIRED)
    in_review = update_required.transition(WorkflowState.IN_REVIEW)
    approved = in_review.transition(WorkflowState.APPROVED)
    released = approved.transition(WorkflowState.RELEASED)

    assert released.state is WorkflowState.RELEASED
