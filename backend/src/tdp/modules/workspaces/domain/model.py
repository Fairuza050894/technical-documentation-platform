import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from tdp.modules.workspaces.domain.errors import (
    DefaultWorkspaceArchiveError,
    InvalidWorkspaceDescriptionError,
    InvalidWorkspaceIdError,
    InvalidWorkspaceKeyError,
    InvalidWorkspaceNameError,
    WorkspaceAlreadyArchivedError,
)

DEFAULT_WORKSPACE_ID = "00000000-0000-4000-8000-000000000001"
DEFAULT_WORKSPACE_KEY = "GENERAL"
DEFAULT_WORKSPACE_NAME = "General Workspace"

_WORKSPACE_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{1,19}$")


class WorkspaceStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True, slots=True)
class WorkspaceId:
    value: UUID

    @classmethod
    def new(cls) -> "WorkspaceId":
        return cls(uuid4())

    @classmethod
    def default(cls) -> "WorkspaceId":
        return cls(UUID(DEFAULT_WORKSPACE_ID))

    @classmethod
    def from_string(cls, value: str) -> "WorkspaceId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidWorkspaceIdError("Workspace ID must be a valid UUID.") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class WorkspaceKey:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not _WORKSPACE_KEY_PATTERN.fullmatch(normalized):
            raise InvalidWorkspaceKeyError(
                "Workspace key must contain 2-20 uppercase letters, numbers, or hyphens."
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class WorkspaceName:
    value: str

    def __post_init__(self) -> None:
        normalized = " ".join(self.value.split())
        if not 3 <= len(normalized) <= 80:
            raise InvalidWorkspaceNameError("Workspace name must contain 3-80 characters.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class WorkspaceDescription:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if len(normalized) > 500:
            raise InvalidWorkspaceDescriptionError(
                "Workspace description must not exceed 500 characters."
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(slots=True)
class Workspace:
    id: WorkspaceId
    key: WorkspaceKey
    name: WorkspaceName
    description: WorkspaceDescription
    status: WorkspaceStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        key: WorkspaceKey,
        name: WorkspaceName,
        description: WorkspaceDescription,
        now: datetime | None = None,
    ) -> "Workspace":
        created_at = now or datetime.now(UTC)
        return cls(
            id=WorkspaceId.new(),
            key=key,
            name=name,
            description=description,
            status=WorkspaceStatus.ACTIVE,
            created_at=created_at,
            updated_at=created_at,
        )

    @classmethod
    def default(cls, *, now: datetime | None = None) -> "Workspace":
        created_at = now or datetime.now(UTC)
        return cls(
            id=WorkspaceId.default(),
            key=WorkspaceKey(DEFAULT_WORKSPACE_KEY),
            name=WorkspaceName(DEFAULT_WORKSPACE_NAME),
            description=WorkspaceDescription(
                "Default workspace for projects created before workspace management was introduced."
            ),
            status=WorkspaceStatus.ACTIVE,
            created_at=created_at,
            updated_at=created_at,
        )

    def archive(self, *, now: datetime | None = None) -> None:
        if str(self.id) == DEFAULT_WORKSPACE_ID:
            raise DefaultWorkspaceArchiveError("The default workspace cannot be archived.")
        if self.status is WorkspaceStatus.ARCHIVED:
            raise WorkspaceAlreadyArchivedError(f"Workspace {self.id} is already archived.")
        self.status = WorkspaceStatus.ARCHIVED
        self.updated_at = now or datetime.now(UTC)
