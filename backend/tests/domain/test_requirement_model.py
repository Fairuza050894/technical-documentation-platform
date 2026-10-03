from datetime import UTC, datetime

import pytest

from tdp.modules.requirements.domain.errors import InvalidRequirementStatusTransitionError
from tdp.modules.requirements.domain.model import (
    Requirement,
    RequirementStatus,
    RequirementType,
)

WORKSPACE_ID = "11111111-1111-4111-8111-111111111111"
PROJECT_ID = "22222222-2222-4222-8222-222222222222"


def requirement() -> Requirement:
    return Requirement.create(
        workspace_id=WORKSPACE_ID,
        project_id=PROJECT_ID,
        key="REQ-001",
        requirement_type=RequirementType.FUNCTIONAL,
        title="Validate shipment inspection",
        statement="The system shall validate shipment inspection before departure.",
        acceptance_criteria=("Inspection is complete before departure.",),
        rationale="Prevent incomplete dispatch.",
        feature_id=None,
        created_by="Technical Writer [local:writer]",
        now=datetime(2026, 10, 3, tzinfo=UTC),
    )


def test_requirement_revision_returns_approved_requirement_to_draft() -> None:
    item = requirement()
    item.approve()

    item.revise(
        title="Validate shipment inspection workflow",
        statement="The system shall validate all mandatory shipment inspection checks before departure.",
        acceptance_criteria=("All mandatory checks are complete before departure.",),
        rationale="Keep dispatch evidence current.",
        feature_id=None,
    )

    assert item.revision == 2
    assert item.status is RequirementStatus.DRAFT


def test_retired_requirement_cannot_be_revised() -> None:
    item = requirement()
    item.retire()

    with pytest.raises(InvalidRequirementStatusTransitionError):
        item.revise(
            title=item.title,
            statement=item.statement,
            acceptance_criteria=item.acceptance_criteria,
            rationale=item.rationale,
            feature_id=None,
        )
