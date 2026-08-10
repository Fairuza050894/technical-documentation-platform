from typing import ClassVar


class ReadinessError(Exception):
    """Base error for deterministic document readiness queries."""

    code: ClassVar[str] = "READINESS_ERROR"


class ReadinessProjectNotFoundError(ReadinessError):
    code = "READINESS_PROJECT_NOT_FOUND"


class InvalidReadinessDocumentTypeError(ReadinessError):
    code = "INVALID_READINESS_DOCUMENT_TYPE"
