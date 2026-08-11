from typing import Any, ClassVar


class DocumentError(Exception):
    """Base error for deterministic document lifecycle failures."""

    code: ClassVar[str] = "DOCUMENT_ERROR"


class InvalidDocumentIdError(DocumentError):
    code = "INVALID_DOCUMENT_ID"


class InvalidDocumentVersionIdError(DocumentError):
    code = "INVALID_DOCUMENT_VERSION_ID"


class InvalidWorkflowEventIdError(DocumentError):
    code = "INVALID_WORKFLOW_EVENT_ID"


class InvalidDocumentVersionNumberError(DocumentError):
    code = "INVALID_DOCUMENT_VERSION_NUMBER"


class InvalidDocumentActorError(DocumentError):
    code = "INVALID_DOCUMENT_ACTOR"


class InvalidDocumentCommentError(DocumentError):
    code = "INVALID_DOCUMENT_COMMENT"


class InvalidDocumentRevisionReasonError(DocumentError):
    code = "INVALID_DOCUMENT_REVISION_REASON"


class InvalidDocumentWorkflowTransitionError(DocumentError):
    code = "INVALID_DOCUMENT_WORKFLOW_TRANSITION"


class DocumentProjectNotFoundError(DocumentError):
    code = "DOCUMENT_PROJECT_NOT_FOUND"


class DocumentProjectArchivedError(DocumentError):
    code = "DOCUMENT_PROJECT_ARCHIVED"


class DocumentSourceNotFoundError(DocumentError):
    code = "DOCUMENT_SOURCE_NOT_FOUND"


class DocumentSnapshotNotFoundError(DocumentError):
    code = "DOCUMENT_SNAPSHOT_NOT_FOUND"


class InvalidDocumentGenerationError(DocumentError):
    code = "INVALID_DOCUMENT_GENERATION"


class DocumentNotFoundError(DocumentError):
    code = "DOCUMENT_NOT_FOUND"


class DocumentVersionNotFoundError(DocumentError):
    code = "DOCUMENT_VERSION_NOT_FOUND"


class InvalidDocumentVersionComparisonError(DocumentError):
    code = "INVALID_DOCUMENT_VERSION_COMPARISON"


class UnsupportedEnterpriseDocumentProfileError(DocumentError):
    code = "UNSUPPORTED_ENTERPRISE_DOCUMENT_PROFILE"


class EnterpriseDocumentGenerationBlockedError(DocumentError):
    code = "ENTERPRISE_DOCUMENT_GENERATION_BLOCKED"

    def __init__(
        self,
        *,
        document_type: str,
        readiness_state: str,
        policy_version: str,
        findings: tuple[Any, ...],
    ) -> None:
        self.document_type = document_type
        self.readiness_state = readiness_state
        self.policy_version = policy_version
        self.findings = findings
        super().__init__(
            f"{document_type} generation is blocked by the canonical readiness policy."
        )
