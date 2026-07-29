from collections.abc import Mapping

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from tdp.modules.projects.domain.errors import (
    InvalidProjectDescriptionError,
    InvalidProjectIdError,
    InvalidProjectKeyError,
    InvalidProjectNameError,
    InvalidWorkspaceTypeError,
    ProjectAlreadyArchivedError,
    ProjectError,
    ProjectKeyAlreadyExistsError,
    ProjectNotFoundError,
)

_ERROR_STATUS: Mapping[type[ProjectError], int] = {
    InvalidProjectIdError: 422,
    InvalidProjectKeyError: 422,
    InvalidProjectNameError: 422,
    InvalidProjectDescriptionError: 422,
    InvalidWorkspaceTypeError: 422,
    ProjectKeyAlreadyExistsError: 409,
    ProjectNotFoundError: 404,
    ProjectAlreadyArchivedError: 409,
}


async def project_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ProjectError):
        raise exc

    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=_ERROR_STATUS.get(type(exc), 400),
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "details": [],
                "requestId": request_id,
            }
        },
        headers={"X-Request-ID": request_id},
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
