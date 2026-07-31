from dataclasses import dataclass

from tdp.modules.workspaces.domain.model import Workspace


@dataclass(frozen=True, slots=True)
class WorkspaceDto:
    id: str
    key: str
    name: str
    description: str
    status: str
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(cls, workspace: Workspace) -> "WorkspaceDto":
        return cls(
            id=str(workspace.id),
            key=str(workspace.key),
            name=str(workspace.name),
            description=str(workspace.description),
            status=workspace.status.value,
            created_at=workspace.created_at.isoformat(),
            updated_at=workspace.updated_at.isoformat(),
        )
