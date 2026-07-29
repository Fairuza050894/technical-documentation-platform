from datetime import UTC, datetime

import pytest

from tdp.modules.documents.domain.errors import InvalidDocumentWorkflowTransitionError
from tdp.modules.documents.domain.model import (
    DocumentId,
    DocumentStatus,
    DocumentVersion,
    DocumentVersionNumber,
)


def build_version() -> DocumentVersion:
    return DocumentVersion.create(
        document_id=DocumentId.new(),
        project_id="project-1",
        source_id="source-1",
        target_run_id="run-1",
        baseline_run_id=None,
        version_number=DocumentVersionNumber.first(),
        title="Technical Source Overview",
        file_name="overview-v1.0.md",
        content="# Overview\n",
        operation_count=1,
        schema_count=1,
        breaking_change_count=0,
        revision_reason="Initial version",
        created_by="Technical Writer",
        now=datetime(2026, 7, 29, 9, 0, tzinfo=UTC),
    )


def test_document_version_follows_review_and_approval_transitions() -> None:
    version = build_version()

    generated = version.generated_event()
    submitted = version.submit_for_review(actor="Technical Writer")
    approved = version.approve(actor="Lead Reviewer", comment="Verified against source.")
    superseded = version.supersede(actor="Lead Reviewer", comment="A newer version is approved.")

    assert generated.previous_status is None
    assert generated.new_status is DocumentStatus.DRAFT
    assert submitted.previous_status is DocumentStatus.DRAFT
    assert approved.previous_status is DocumentStatus.IN_REVIEW
    assert superseded.previous_status is DocumentStatus.APPROVED
    assert version.status is DocumentStatus.SUPERSEDED


def test_document_version_rejects_invalid_transition() -> None:
    version = build_version()

    with pytest.raises(InvalidDocumentWorkflowTransitionError):
        version.approve(actor="Lead Reviewer")


def test_document_version_number_increments_minor_revision() -> None:
    first = DocumentVersionNumber.first()

    assert str(first) == "1.0"
    assert str(first.next_minor()) == "1.1"
