from typing import ClassVar


class SourceError(Exception):
    """Base error for technical source failures."""

    code: ClassVar[str] = "SOURCE_ERROR"


class InvalidSourceIdError(SourceError):
    code = "INVALID_SOURCE_ID"


class InvalidSourceProjectIdError(SourceError):
    code = "INVALID_SOURCE_PROJECT_ID"


class InvalidSourceNameError(SourceError):
    code = "INVALID_SOURCE_NAME"


class InvalidSourceFileNameError(SourceError):
    code = "INVALID_SOURCE_FILE_NAME"


class InvalidSourceChecksumError(SourceError):
    code = "INVALID_SOURCE_CHECKSUM"


class InvalidArtifactKeyError(SourceError):
    code = "INVALID_ARTIFACT_KEY"


class UnsupportedSourceFileError(SourceError):
    code = "UNSUPPORTED_SOURCE_FILE"


class EmptySourceFileError(SourceError):
    code = "EMPTY_SOURCE_FILE"


class SourceFileTooLargeError(SourceError):
    code = "SOURCE_FILE_TOO_LARGE"


class InvalidOpenApiDocumentError(SourceError):
    code = "INVALID_OPENAPI_DOCUMENT"


class UnsupportedOpenApiVersionError(SourceError):
    code = "UNSUPPORTED_OPENAPI_VERSION"


class SourceProjectNotFoundError(SourceError):
    code = "SOURCE_PROJECT_NOT_FOUND"


class SourceProjectArchivedError(SourceError):
    code = "SOURCE_PROJECT_ARCHIVED"


class SourceNameAlreadyExistsError(SourceError):
    code = "SOURCE_NAME_ALREADY_EXISTS"


class SourceNotFoundError(SourceError):
    code = "SOURCE_NOT_FOUND"


class SourceAlreadyArchivedError(SourceError):
    code = "SOURCE_ALREADY_ARCHIVED"
