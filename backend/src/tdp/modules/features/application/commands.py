from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateFeatureCommand:
    workspace_id: str
    project_id: str
    key: str
    name: str
    description: str
    kind: str
    owner: str
