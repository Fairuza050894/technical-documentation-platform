from typing import ClassVar


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
