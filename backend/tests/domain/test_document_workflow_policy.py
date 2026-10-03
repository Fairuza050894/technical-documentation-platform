import pytest

from tdp.modules.documents.domain.errors import DocumentSeparationOfDutiesError
from tdp.modules.documents.domain.workflow_policy import ApprovalContext, DocumentApprovalPolicy


def test_verified_identity_cannot_self_approve_authored_version() -> None:
    policy = DocumentApprovalPolicy()

    with pytest.raises(DocumentSeparationOfDutiesError):
        policy.validate(
            ApprovalContext(
                author_actor="Alice [oidc:alice]",
                reviewer_actor="Alice [oidc:alice]",
                verified_identity=True,
            )
        )


def test_verified_independent_reviewer_can_approve() -> None:
    policy = DocumentApprovalPolicy()

    policy.validate(
        ApprovalContext(
            author_actor="Alice [oidc:alice]",
            reviewer_actor="Bob [oidc:bob]",
            verified_identity=True,
        )
    )


def test_local_development_identity_keeps_controlled_evaluation_flow() -> None:
    policy = DocumentApprovalPolicy()

    policy.validate(
        ApprovalContext(
            author_actor="Technical Writer [local:tw]",
            reviewer_actor="Technical Writer [local:tw]",
            verified_identity=False,
        )
    )
