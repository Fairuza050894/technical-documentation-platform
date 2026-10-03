from tdp.modules.changes.domain.impact import (
    DeterministicImpactPolicy,
    ImpactAction,
    ImpactPriority,
)
from tdp.modules.changes.domain.model import (
    Change,
    ChangeKind,
    ChangeSeverity,
    Comparison,
)


def comparison(severity: ChangeSeverity) -> Comparison:
    return Comparison(
        project_id="project-1",
        baseline_run_id="run-1",
        target_run_id="run-2",
        changes=(
            Change(
                entity_type="OPERATION",
                entity_key="POST /shipments",
                kind=ChangeKind.MODIFIED,
                severity=severity,
                summary="Operation changed.",
                before_pointer="#/paths/shipments/post",
                after_pointer="#/paths/shipments/post",
                details={},
            ),
        ),
    )


def test_breaking_change_requires_governed_approval() -> None:
    assessment = DeterministicImpactPolicy().assess(comparison(ChangeSeverity.BREAKING))

    assert assessment.approval_required is True
    assert assessment.requirement_revalidation_required is True
    assert assessment.highest_priority is ImpactPriority.P1
    assert any(item.action is ImpactAction.APPROVAL_REQUIRED for item in assessment.items)
    assert {item.document_type for item in assessment.items} >= {
        "TECHNICAL_SOURCE_OVERVIEW",
        "LLD",
        "HLD",
        "UAT_EVIDENCE",
        "USER_GUIDE",
        "AS_BUILT",
    }


def test_non_breaking_change_requires_review_not_approval() -> None:
    assessment = DeterministicImpactPolicy().assess(comparison(ChangeSeverity.NON_BREAKING))

    assert assessment.approval_required is False
    assert assessment.highest_priority is ImpactPriority.P3
    assert all(item.action is ImpactAction.REVIEW_REQUIRED for item in assessment.items)
