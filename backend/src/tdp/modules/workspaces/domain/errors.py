from typing import ClassVar


class WorkspaceError(Exception):
    """Base error for workspace domain and application failures."""

    code: ClassVar[str] = "WORKSPACE_ERROR"


class InvalidWorkspaceIdError(WorkspaceError):
    code = "INVALID_WORKSPACE_ID"


class InvalidWorkspaceKeyError(WorkspaceError):
    code = "INVALID_WORKSPACE_KEY"


class InvalidWorkspaceNameError(WorkspaceError):
    code = "INVALID_WORKSPACE_NAME"


class InvalidWorkspaceDescriptionError(WorkspaceError):
    code = "INVALID_WORKSPACE_DESCRIPTION"


class WorkspaceKeyAlreadyExistsError(WorkspaceError):
    code = "WORKSPACE_KEY_ALREADY_EXISTS"


class WorkspaceNotFoundError(WorkspaceError):
    code = "WORKSPACE_NOT_FOUND"


class WorkspaceAlreadyArchivedError(WorkspaceError):
    code = "WORKSPACE_ALREADY_ARCHIVED"


class WorkspaceArchivedError(WorkspaceError):
    code = "WORKSPACE_ARCHIVED"


class DefaultWorkspaceArchiveError(WorkspaceError):
    code = "DEFAULT_WORKSPACE_ARCHIVE_FORBIDDEN"
