from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateProjectCommand:
    key: str
    name: str
    description: str
    workspace_type: str
    workspace_id: str | None = None
    ownership_type: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateProjectCommand:
    name: str | None = None
    description: str | None = None