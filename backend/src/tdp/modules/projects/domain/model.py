import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from tdp.modules.projects.domain.errors import (
    InvalidProjectDescriptionError,
    InvalidProjectIdError,
    InvalidProjectKeyError,
    InvalidProjectNameError,
    InvalidProjectWorkspaceIdError,
    ProjectAlreadyArchivedError,
)
from tdp.modules.workspaces.domain.model import DEFAULT_WORKSPACE_ID

_PROJECT_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{1,19}$")


class ProjectStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class WorkspaceType(StrEnum):
    """Deprecated project classification retained for API and data migration compatibility."""

    DEMO = "DEMO"
    PERSONAL = "PERSONAL"
    ENTERPRISE = "ENTERPRISE"


class OwnershipType(StrEnum):
    PERSONAL = "PERSONAL"
    TEAM = "TEAM"

    @classmethod
    def from_legacy_workspace_type(cls, value: WorkspaceType) -> "OwnershipType":
        return cls.TEAM if value is WorkspaceType.ENTERPRISE else cls.PERSONAL


@dataclass(frozen=True, slots=True)
class ProjectId:
    value: UUID

    @classmethod
    def new(cls) -> "ProjectId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "ProjectId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidProjectIdError("Project ID must be a valid UUID.") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class ProjectKey:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not _PROJECT_KEY_PATTERN.fullmatch(normalized):
            raise InvalidProjectKeyError(
                "Project key must contain 2-20 uppercase letters, numbers, or hyphens."
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ProjectName:
    value: str

    def __post_init__(self) -> None:
        normalized = " ".join(self.value.split())
        if not 3 <= len(normalized) <= 80:
            raise InvalidProjectNameError("Project name must contain 3-80 characters.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ProjectDescription:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if len(normalized) > 500:
            raise InvalidProjectDescriptionError(
                "Project description must not exceed 500 characters."
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(slots=True)
class Project:
    id: ProjectId
    key: ProjectKey
    name: ProjectName
    description: ProjectDescription
    workspace_type: WorkspaceType
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    workspace_id: str = DEFAULT_WORKSPACE_ID
    ownership_type: OwnershipType = OwnershipType.PERSONAL

    def __post_init__(self) -> None:
        try:
            UUID(self.workspace_id)
        except ValueError as exc:
            raise InvalidProjectWorkspaceIdError(
                "Project workspace reference must be a valid UUID."
            ) from exc

    @classmethod
    def create(
        cls,
        *,
        key: ProjectKey,
        name: ProjectName,
        description: ProjectDescription,
        workspace_type: WorkspaceType = WorkspaceType.PERSONAL,
        workspace_id: str = DEFAULT_WORKSPACE_ID,
        ownership_type: OwnershipType | None = None,
        now: datetime | None = None,
    ) -> "Project":
        created_at = now or datetime.now(UTC)
        resolved_ownership = ownership_type or OwnershipType.from_legacy_workspace_type(
            workspace_type
        )
        return cls(
            id=ProjectId.new(),
            key=key,
            name=name,
            description=description,
            workspace_type=workspace_type,
            status=ProjectStatus.ACTIVE,
            created_at=created_at,
            updated_at=created_at,
            workspace_id=workspace_id,
            ownership_type=resolved_ownership,
        )

    def archive(self, *, now: datetime | None = None) -> None:
        if self.status is ProjectStatus.ARCHIVED:
            raise ProjectAlreadyArchivedError(f"Project {self.id} is already archived.")
        self.status = ProjectStatus.ARCHIVED
        self.updated_at = now or datetime.now(UTC)
