import asyncio

from tdp.modules.features.domain.model import (
    Feature,
    FeatureDescription,
    FeatureKey,
    FeatureKind,
    FeatureName,
    FeatureOwner,
    create_documentation_map,
)
from tdp.modules.features.infrastructure.sqlite_repository import SqliteFeatureRepository
from tdp.modules.projects.domain.model import (
    Project,
    ProjectDescription,
    ProjectKey,
    ProjectName,
    WorkspaceType,
)
from tdp.modules.projects.infrastructure.sqlite_repository import SqliteProjectRepository


def test_sqlite_feature_repository_persists_registry_and_map(tmp_path) -> None:
    database_path = tmp_path / "features.sqlite3"
    project_repository = SqliteProjectRepository(database_path)
    feature_repository = SqliteFeatureRepository(database_path)
    project = Project.create(
        key=ProjectKey("ERP-CORE"),
        name=ProjectName("ERP Core"),
        description=ProjectDescription("Core ERP capabilities"),
        workspace_type=WorkspaceType.PERSONAL,
    )
    asyncio.run(project_repository.add(project))
    feature = Feature.create(
        project_id=str(project.id),
        key=FeatureKey("PAYMENT"),
        name=FeatureName("Payment Processing"),
        description=FeatureDescription("Payment capture and verification"),
        kind=FeatureKind.FEATURE,
        owner=FeatureOwner("ERP Team"),
    )

    asyncio.run(feature_repository.add(feature, create_documentation_map(feature)))
    loaded = asyncio.run(feature_repository.get(feature.id))
    documentation_map = asyncio.run(feature_repository.list_documentation_map(feature.id))

    assert loaded == feature
    assert len(documentation_map) == 8
    assert sum(item.requirement.value == "REQUIRED" for item in documentation_map) == 4
