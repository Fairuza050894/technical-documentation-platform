from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateProjectCommand:
    key: str
    name: str
    description: str
    workspace_type: str
