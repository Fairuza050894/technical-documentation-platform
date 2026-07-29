from typing import ClassVar


class DocumentError(Exception):
    """Base error for deterministic generated document failures."""

    code: ClassVar[str] = "DOCUMENT_ERROR"


class InvalidDocumentIdError(DocumentError):
    code = "INVALID_DOCUMENT_ID"


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
