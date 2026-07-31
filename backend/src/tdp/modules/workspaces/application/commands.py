from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateWorkspaceCommand:
    key: str
    name: str
    description: str
