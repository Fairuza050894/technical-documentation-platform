from tdp.modules.changes.domain.impact import (
    DeterministicChangeImpactPolicy,
    ImpactLevel,
)
from tdp.modules.changes.domain.model import (
    Change,
    ChangeKind,
    ChangeSeverity,
    Comparison,
)


def _comparison(change: Change) -> Comparison:
    return Comparison(
        project_id="11111111-1111-4111-8111-111111111111",
        baseline_run_id="22222222-2222-4222-8222-222222222222",
        target_run_id="33333333-3333-4333-8333-333333333333",
        changes=(change,),
    )


def test_breaking_change_requires_requirement_test_and_document_review() -> None:
    policy = DeterministicChangeImpactPolicy()
    assessment = policy.assess(
        _comparison(
            Change(
                entity_type="OPERATION",
                entity_key="POST /orders",
                kind=ChangeKind.REMOVED,
                severity=ChangeSeverity.BREAKING,
                summary="Operation POST /orders was removed.",
                before_pointer="#/paths/~1orders/post",
                after_pointer="",
                details={},
            )
        )
    )

    assert assessment.level is ImpactLevel.CRITICAL
    assert assessment.requirement_review_required is True
    assert assessment.test_execution_required is True
    assert assessment.required_document_types == (
        "HLD",
        "LLD",
        "AS_BUILT",
        "USER_GUIDE",
        "UAT_EVIDENCE",
    )


def test_security_contract_change_escalates_architecture_review() -> None:
    policy = DeterministicChangeImpactPolicy()
    assessment = policy.assess(
        _comparison(
            Change(
                entity_type="OPERATION",
                entity_key="GET /profile",
                kind=ChangeKind.MODIFIED,
                severity=ChangeSeverity.POTENTIALLY_BREAKING,
                summary="Operation GET /profile changed.",
                before_pointer="#/paths/~1profile/get",
                after_pointer="#/paths/~1profile/get",
                details={
                    "security_before": ["bearerAuth"],
                    "security_after": ["oauth2"],
                },
            )
        )
    )

    assert assessment.level is ImpactLevel.HIGH
    assert "HLD" in assessment.required_document_types
    assert assessment.requirement_review_required is True
