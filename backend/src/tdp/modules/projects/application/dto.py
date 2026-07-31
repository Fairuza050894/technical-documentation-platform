from dataclasses import dataclass

from tdp.modules.projects.domain.model import Project


@dataclass(frozen=True, slots=True)
class ProjectDto:
    id: str
    key: str
    name: str
    description: str
    workspace_type: str
    workspace_id: str
    ownership_type: str
    status: str
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(cls, project: Project) -> "ProjectDto":
        return cls(
            id=str(project.id),
            key=str(project.key),
            name=str(project.name),
            description=str(project.description),
            workspace_type=project.workspace_type.value,
            workspace_id=project.workspace_id,
            ownership_type=project.ownership_type.value,
            status=project.status.value,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
        )
