from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateWorkspaceCommand:
    key: str
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class UpdateWorkspaceCommand:
    name: str | None = None
    description: str | None = None