from collections.abc import Mapping

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from tdp.modules.catalog.domain.errors import (
    CatalogArtifactIntegrityError,
    CatalogArtifactNotFoundError,
    CatalogError,
    CatalogProjectArchivedError,
    CatalogProjectNotFoundError,
    CatalogSourceArchivedError,
    CatalogSourceNotFoundError,
    InvalidCatalogDocumentError,
    InvalidSynchronizationIdError,
    SynchronizationNotFoundError,
)
from tdp.modules.changes.domain.errors import (
    ChangeDetectionError,
    ComparisonRunNotFoundError,
    InvalidComparisonError,
)
from tdp.modules.documents.domain.errors import (
    DocumentError,
    DocumentNotFoundError,
    DocumentProjectArchivedError,
    DocumentProjectNotFoundError,
    DocumentSnapshotNotFoundError,
    DocumentSourceNotFoundError,
    DocumentVersionNotFoundError,
    InvalidDocumentActorError,
    InvalidDocumentCommentError,
    InvalidDocumentGenerationError,
    InvalidDocumentIdError,
    InvalidDocumentRevisionReasonError,
    InvalidDocumentVersionComparisonError,
    InvalidDocumentVersionIdError,
    InvalidDocumentVersionNumberError,
    InvalidDocumentWorkflowTransitionError,
    InvalidWorkflowEventIdError,
)
from tdp.modules.projects.domain.errors import (
    InvalidOwnershipTypeError,
    InvalidProjectDescriptionError,
    InvalidProjectIdError,
    InvalidProjectKeyError,
    InvalidProjectNameError,
    InvalidProjectWorkspaceIdError,
    InvalidWorkspaceTypeError,
    ProjectAlreadyArchivedError,
    ProjectError,
    ProjectKeyAlreadyExistsError,
    ProjectNotFoundError,
)
from tdp.modules.sources.domain.errors import (
    EmptySourceFileError,
    InvalidArtifactKeyError,
    InvalidOpenApiDocumentError,
    InvalidSourceChecksumError,
    InvalidSourceFileNameError,
    InvalidSourceIdError,
    InvalidSourceNameError,
    InvalidSourceProjectIdError,
    SourceAlreadyArchivedError,
    SourceError,
    SourceFileTooLargeError,
    SourceNameAlreadyExistsError,
    SourceNotFoundError,
    SourceProjectArchivedError,
    SourceProjectNotFoundError,
    UnsupportedOpenApiVersionError,
    UnsupportedSourceFileError,
)
from tdp.modules.workspaces.domain.errors import (
    DefaultWorkspaceArchiveError,
    InvalidWorkspaceDescriptionError,
    InvalidWorkspaceIdError,
    InvalidWorkspaceKeyError,
    InvalidWorkspaceNameError,
    WorkspaceAlreadyArchivedError,
    WorkspaceArchivedError,
    WorkspaceError,
    WorkspaceKeyAlreadyExistsError,
    WorkspaceNotFoundError,
)

_CATALOG_ERROR_STATUS: Mapping[type[CatalogError], int] = {
    InvalidSynchronizationIdError: 422,
    CatalogSourceNotFoundError: 404,
    CatalogSourceArchivedError: 409,
    CatalogProjectNotFoundError: 404,
    CatalogProjectArchivedError: 409,
    CatalogArtifactNotFoundError: 404,
    CatalogArtifactIntegrityError: 409,
    InvalidCatalogDocumentError: 422,
    SynchronizationNotFoundError: 404,
}

_CHANGE_DETECTION_ERROR_STATUS: Mapping[type[ChangeDetectionError], int] = {
    InvalidComparisonError: 422,
    ComparisonRunNotFoundError: 404,
}

_DOCUMENT_ERROR_STATUS: Mapping[type[DocumentError], int] = {
    InvalidDocumentIdError: 422,
    InvalidDocumentVersionIdError: 422,
    InvalidWorkflowEventIdError: 422,
    InvalidDocumentVersionNumberError: 422,
    InvalidDocumentVersionComparisonError: 422,
    InvalidDocumentActorError: 422,
    InvalidDocumentCommentError: 422,
    InvalidDocumentRevisionReasonError: 422,
    InvalidDocumentWorkflowTransitionError: 409,
    DocumentProjectNotFoundError: 404,
    DocumentProjectArchivedError: 409,
    DocumentSourceNotFoundError: 404,
    DocumentSnapshotNotFoundError: 404,
    InvalidDocumentGenerationError: 422,
    DocumentNotFoundError: 404,
    DocumentVersionNotFoundError: 404,
}

_PROJECT_ERROR_STATUS: Mapping[type[ProjectError], int] = {
    InvalidProjectIdError: 422,
    InvalidProjectKeyError: 422,
    InvalidProjectNameError: 422,
    InvalidProjectDescriptionError: 422,
    InvalidWorkspaceTypeError: 422,
    InvalidOwnershipTypeError: 422,
    InvalidProjectWorkspaceIdError: 422,
    ProjectKeyAlreadyExistsError: 409,
    ProjectNotFoundError: 404,
    ProjectAlreadyArchivedError: 409,
}

_WORKSPACE_ERROR_STATUS: Mapping[type[WorkspaceError], int] = {
    InvalidWorkspaceIdError: 422,
    InvalidWorkspaceKeyError: 422,
    InvalidWorkspaceNameError: 422,
    InvalidWorkspaceDescriptionError: 422,
    WorkspaceKeyAlreadyExistsError: 409,
    WorkspaceNotFoundError: 404,
    WorkspaceAlreadyArchivedError: 409,
    WorkspaceArchivedError: 409,
    DefaultWorkspaceArchiveError: 409,
}

_SOURCE_ERROR_STATUS: Mapping[type[SourceError], int] = {
    InvalidSourceIdError: 422,
    InvalidSourceProjectIdError: 422,
    InvalidSourceNameError: 422,
    InvalidSourceFileNameError: 422,
    InvalidSourceChecksumError: 422,
    InvalidArtifactKeyError: 422,
    UnsupportedSourceFileError: 415,
    EmptySourceFileError: 422,
    SourceFileTooLargeError: 413,
    InvalidOpenApiDocumentError: 422,
    UnsupportedOpenApiVersionError: 422,
    SourceProjectNotFoundError: 404,
    SourceProjectArchivedError: 409,
    SourceNameAlreadyExistsError: 409,
    SourceNotFoundError: 404,
    SourceAlreadyArchivedError: 409,
}


async def catalog_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, CatalogError):
        raise exc
    return _error_response(request, exc.code, str(exc), _CATALOG_ERROR_STATUS.get(type(exc), 400))


async def change_detection_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ChangeDetectionError):
        raise exc
    return _error_response(
        request,
        exc.code,
        str(exc),
        _CHANGE_DETECTION_ERROR_STATUS.get(type(exc), 400),
    )


async def document_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DocumentError):
        raise exc
    return _error_response(
        request,
        exc.code,
        str(exc),
        _DOCUMENT_ERROR_STATUS.get(type(exc), 400),
    )


async def project_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ProjectError):
        raise exc
    return _error_response(request, exc.code, str(exc), _PROJECT_ERROR_STATUS.get(type(exc), 400))


async def source_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, SourceError):
        raise exc
    return _error_response(request, exc.code, str(exc), _SOURCE_ERROR_STATUS.get(type(exc), 400))


async def workspace_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, WorkspaceError):
        raise exc
    return _error_response(
        request,
        exc.code,
        str(exc),
        _WORKSPACE_ERROR_STATUS.get(type(exc), 400),
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc

    request_id = getattr(request.state, "request_id", "unknown")
    details = [
        {
            "field": ".".join(str(part) for part in error["loc"] if part != "body"),
            "reason": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "REQUEST_VALIDATION_ERROR",
                "message": "The request contains invalid data.",
                "details": details,
                "requestId": request_id,
            }
        },
        headers={"X-Request-ID": request_id},
    )


def _error_response(request: Request, code: str, message: str, status_code: int) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": [],
                "requestId": request_id,
            }
        },
        headers={"X-Request-ID": request_id},
    )
