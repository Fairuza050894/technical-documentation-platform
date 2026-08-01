import asyncio

from tdp.modules.features.application.commands import CreateFeatureCommand
from tdp.modules.features.application.service import FeatureApplicationService
from tdp.modules.features.domain.model import (
    Feature,
    FeatureDocumentationMapItem,
    FeatureId,
    FeatureKey,
)
from tdp.modules.projects.domain.model import (
    OwnershipType,
    Project,
    ProjectDescription,
    ProjectId,
    ProjectKey,
    ProjectName,
    WorkspaceType,
)
from tdp.modules.workspaces.domain.model import (
    Workspace,
    WorkspaceDescription,
    WorkspaceId,
    WorkspaceKey,
    WorkspaceName,
)


class InMemoryFeatureRepository:
    def __init__(self) -> None:
        self.features: dict[str, Feature] = {}
        self.maps: dict[str, list[FeatureDocumentationMapItem]] = {}

    async def add(
        self,
        feature: Feature,
        documentation_map: list[FeatureDocumentationMapItem],
    ) -> None:
        self.features[str(feature.id)] = feature
        self.maps[str(feature.id)] = documentation_map

    async def update(self, feature: Feature) -> None:
        self.features[str(feature.id)] = feature

    async def get(self, feature_id: FeatureId) -> Feature | None:
        return self.features.get(str(feature_id))

    async def get_by_project_key(
        self,
        project_id: str,
        key: FeatureKey,
    ) -> Feature | None:
        return next(
            (
                feature
                for feature in self.features.values()
                if feature.project_id == project_id and feature.key == key
            ),
            None,
        )

    async def list_by_project(self, project_id: str) -> list[Feature]:
        return [feature for feature in self.features.values() if feature.project_id == project_id]

    async def list_documentation_map(
        self,
        feature_id: FeatureId,
    ) -> list[FeatureDocumentationMapItem]:
        return self.maps.get(str(feature_id), [])


class InMemoryProjectRepository:
    def __init__(self, project: Project) -> None:
        self.project = project

    async def get(self, project_id: ProjectId) -> Project | None:
        return self.project if self.project.id == project_id else None


class InMemoryWorkspaceRepository:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    async def get(self, workspace_id: WorkspaceId) -> Workspace | None:
        return self.workspace if self.workspace.id == workspace_id else None


WORKSPACE = Workspace.create(
    key=WorkspaceKey("ERP"),
    name=WorkspaceName("ERP Workspace"),
    description=WorkspaceDescription("ERP systems"),
)
PROJECT = Project.create(
    key=ProjectKey("ERP-CORE"),
    name=ProjectName("ERP Core"),
    description=ProjectDescription("Core ERP capabilities"),
    workspace_type=WorkspaceType.ENTERPRISE,
    workspace_id=str(WORKSPACE.id),
    ownership_type=OwnershipType.TEAM,
)


def service() -> FeatureApplicationService:
    return FeatureApplicationService(
        InMemoryFeatureRepository(),
        InMemoryProjectRepository(PROJECT),
        InMemoryWorkspaceRepository(WORKSPACE),
    )


def command() -> CreateFeatureCommand:
    return CreateFeatureCommand(
        workspace_id=str(WORKSPACE.id),
        project_id=str(PROJECT.id),
        key="payments",
        name="Payment Processing",
        description="Payment capture and verification",
        kind="FEATURE",
        owner="ERP Team",
    )


def test_create_feature_builds_deterministic_documentation_map() -> None:
    application = service()

    created = asyncio.run(application.create(command()))
    map_items = asyncio.run(
        application.documentation_map(
            str(WORKSPACE.id),
            str(PROJECT.id),
            created.id,
        )
    )

    assert created.key == "PAYMENTS"
    assert created.documentation_coverage.required_total == 4
    assert created.documentation_coverage.missing_required == 4
    assert len(map_items) == 8
    assert {item.policy_key for item in map_items} == {"feature-documentation-baseline-v1"}


def test_archive_feature_preserves_documentation_map() -> None:
    application = service()
    created = asyncio.run(application.create(command()))

    archived = asyncio.run(application.archive(str(WORKSPACE.id), str(PROJECT.id), created.id))
    listed = asyncio.run(application.list_features(str(WORKSPACE.id), str(PROJECT.id)))

    assert archived.status == "ARCHIVED"
    assert listed == [archived]
