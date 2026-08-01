from tdp.modules.features.application.commands import CreateFeatureCommand
from tdp.modules.features.application.dto import (
    FeatureDocumentationMapItemDto,
    FeatureDto,
)
from tdp.modules.features.domain.errors import (
    FeatureKeyAlreadyExistsError,
    FeatureNotFoundError,
    FeatureProjectArchivedError,
    FeatureProjectNotFoundError,
    FeatureWorkspaceMismatchError,
    InvalidFeatureKindError,
)
from tdp.modules.features.domain.model import (
    Feature,
    FeatureDescription,
    FeatureId,
    FeatureKey,
    FeatureKind,
    FeatureName,
    FeatureOwner,
    create_documentation_map,
)
from tdp.modules.features.domain.repository import FeatureRepository
from tdp.modules.projects.domain.model import Project, ProjectId, ProjectStatus
from tdp.modules.projects.domain.repository import ProjectRepository
from tdp.modules.workspaces.domain.model import WorkspaceId, WorkspaceStatus
from tdp.modules.workspaces.domain.repository import WorkspaceRepository


class FeatureApplicationService:
    def __init__(
        self,
        repository: FeatureRepository,
        project_repository: ProjectRepository,
        workspace_repository: WorkspaceRepository,
    ) -> None:
        self._repository = repository
        self._project_repository = project_repository
        self._workspace_repository = workspace_repository

    async def create(self, command: CreateFeatureCommand) -> FeatureDto:
        project = await self._require_project(
            command.workspace_id,
            command.project_id,
            writable=True,
        )
        key = FeatureKey(command.key)
        if await self._repository.get_by_project_key(command.project_id, key) is not None:
            raise FeatureKeyAlreadyExistsError(
                f"Feature key {key} is already in use inside project {command.project_id}."
            )
        try:
            kind = FeatureKind(command.kind)
        except ValueError as exc:
            raise InvalidFeatureKindError(f"Feature kind {command.kind} is not supported.") from exc

        feature = Feature.create(
            project_id=str(project.id),
            key=key,
            name=FeatureName(command.name),
            description=FeatureDescription(command.description),
            kind=kind,
            owner=FeatureOwner(command.owner),
        )
        documentation_map = create_documentation_map(feature)
        await self._repository.add(feature, documentation_map)
        return FeatureDto.from_domain(feature, documentation_map)

    async def list_features(self, workspace_id: str, project_id: str) -> list[FeatureDto]:
        await self._require_project(workspace_id, project_id, writable=False)
        features = await self._repository.list_by_project(project_id)
        return [await self._to_dto(feature) for feature in features]

    async def get(self, workspace_id: str, project_id: str, feature_id: str) -> FeatureDto:
        await self._require_project(workspace_id, project_id, writable=False)
        feature = await self._get_feature(project_id, feature_id)
        return await self._to_dto(feature)

    async def archive(
        self,
        workspace_id: str,
        project_id: str,
        feature_id: str,
    ) -> FeatureDto:
        await self._require_project(workspace_id, project_id, writable=True)
        feature = await self._get_feature(project_id, feature_id)
        feature.archive()
        await self._repository.update(feature)
        return await self._to_dto(feature)

    async def documentation_map(
        self,
        workspace_id: str,
        project_id: str,
        feature_id: str,
    ) -> list[FeatureDocumentationMapItemDto]:
        await self._require_project(workspace_id, project_id, writable=False)
        feature = await self._get_feature(project_id, feature_id)
        items = await self._repository.list_documentation_map(feature.id)
        return [FeatureDocumentationMapItemDto.from_domain(item) for item in items]

    async def _to_dto(self, feature: Feature) -> FeatureDto:
        documentation_map = await self._repository.list_documentation_map(feature.id)
        return FeatureDto.from_domain(feature, documentation_map)

    async def _get_feature(self, project_id: str, feature_id: str) -> Feature:
        feature = await self._repository.get(FeatureId.from_string(feature_id))
        if feature is None or feature.project_id != project_id:
            raise FeatureNotFoundError(
                f"Feature {feature_id} was not found for project {project_id}."
            )
        return feature

    async def _require_project(
        self,
        workspace_id: str,
        project_id: str,
        *,
        writable: bool,
    ) -> Project:
        project = await self._project_repository.get(ProjectId.from_string(project_id))
        if project is None:
            raise FeatureProjectNotFoundError(f"Project {project_id} was not found.")
        if project.workspace_id != workspace_id:
            raise FeatureWorkspaceMismatchError(
                f"Project {project_id} does not belong to workspace {workspace_id}."
            )
        workspace = await self._workspace_repository.get(WorkspaceId.from_string(workspace_id))
        if workspace is None:
            raise FeatureWorkspaceMismatchError(
                f"Workspace {workspace_id} was not found for project {project_id}."
            )
        if writable and (
            project.status is ProjectStatus.ARCHIVED or workspace.status is WorkspaceStatus.ARCHIVED
        ):
            raise FeatureProjectArchivedError(
                "Features cannot be changed for an archived project or workspace."
            )
        return project
