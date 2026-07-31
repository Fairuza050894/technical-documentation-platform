from typing import ClassVar


class ProjectError(Exception):
    """Base error for project domain and application failures."""

    code: ClassVar[str] = "PROJECT_ERROR"


class InvalidProjectIdError(ProjectError):
    code = "INVALID_PROJECT_ID"


class InvalidProjectKeyError(ProjectError):
    code = "INVALID_PROJECT_KEY"


class InvalidProjectNameError(ProjectError):
    code = "INVALID_PROJECT_NAME"


class InvalidProjectDescriptionError(ProjectError):
    code = "INVALID_PROJECT_DESCRIPTION"


class InvalidWorkspaceTypeError(ProjectError):
    code = "INVALID_WORKSPACE_TYPE"


class InvalidOwnershipTypeError(ProjectError):
    code = "INVALID_OWNERSHIP_TYPE"


class InvalidProjectWorkspaceIdError(ProjectError):
    code = "INVALID_PROJECT_WORKSPACE_ID"


class ProjectKeyAlreadyExistsError(ProjectError):
    code = "PROJECT_KEY_ALREADY_EXISTS"


class ProjectNotFoundError(ProjectError):
    code = "PROJECT_NOT_FOUND"


class ProjectAlreadyArchivedError(ProjectError):
    code = "PROJECT_ALREADY_ARCHIVED"
