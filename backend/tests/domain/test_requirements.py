from datetime import UTC, datetime

import pytest

from tdp.modules.requirements.domain.errors import (
    InvalidTraceRelationError,
    RequirementRetiredError,
)
from tdp.modules.requirements.domain.model import (
    RequirementRevision,
    RequirementStatus,
    RequirementType,
    TraceLink,
    TraceRelation,
    TraceTargetType,
)


def _requirement() -> RequirementRevision:
    return RequirementRevision.create(
        project_id="11111111-1111-4111-8111-111111111111",
        key="REQ-001",
        requirement_type=RequirementType.SYSTEM,
        title="Validate meal allowance request",
        statement="The system shall validate a driver's meal allowance request before approval.",
        owner="Business Analyst",
        feature_id="22222222-2222-4222-8222-222222222222",
        acceptance_criteria=(
            "A request outside the configured policy is rejected with a deterministic reason.",
        ),
        changed_by="Technical Writer [local:tw]",
        change_reason="Initial governed requirement.",
        now=datetime(2026, 10, 3, tzinfo=UTC),
    )


def test_requirement_revisions_are_immutable_and_increment_revision() -> None:
    original = _requirement()

    revised = original.revise(
        title=original.title,
        statement="The system shall validate a driver's meal allowance request before workflow approval.",
        owner=original.owner,
        feature_id=original.feature_id,
        acceptance_criteria=original.acceptance_criteria,
        changed_by="Technical Writer [local:tw]",
        change_reason="Clarify workflow boundary.",
        now=datetime(2026, 10, 4, tzinfo=UTC),
    )

    assert original.revision == 1
    assert revised.revision == 2
    assert revised.requirement_id == original.requirement_id
    assert revised.revision_id != original.revision_id
    assert "workflow approval" not in original.statement
    assert "workflow approval" in revised.statement


def test_retired_requirement_cannot_be_revised() -> None:
    current = _requirement()
    retired = current.retire(
        changed_by="Technical Writer [local:tw]",
        change_reason="Capability was formally retired.",
    )

    assert retired.status is RequirementStatus.RETIRED
    with pytest.raises(RequirementRetiredError):
        retired.revise(
            title=retired.title,
            statement=retired.statement,
            owner=retired.owner,
            feature_id=retired.feature_id,
            acceptance_criteria=retired.acceptance_criteria,
            changed_by="Technical Writer [local:tw]",
            change_reason="Invalid revision attempt.",
        )


def test_trace_relation_must_match_target_type() -> None:
    revision = _requirement()

    with pytest.raises(InvalidTraceRelationError):
        TraceLink.create(
            project_id=revision.project_id,
            requirement_revision_id=revision.revision_id,
            target_type=TraceTargetType.EVIDENCE,
            relation=TraceRelation.DOCUMENTED_BY,
            target_reference="33333333-3333-4333-8333-333333333333",
            verified=True,
            created_by="Technical Writer [local:tw]",
        )


def test_trace_link_records_verified_source_backed_relationship() -> None:
    revision = _requirement()
    link = TraceLink.create(
        project_id=revision.project_id,
        requirement_revision_id=revision.revision_id,
        target_type=TraceTargetType.EVIDENCE,
        relation=TraceRelation.VERIFIED_BY,
        target_reference="33333333-3333-4333-8333-333333333333",
        verified=True,
        created_by="Technical Writer [local:tw]",
    )

    assert link.verified is True
    assert link.relation is TraceRelation.VERIFIED_BY
