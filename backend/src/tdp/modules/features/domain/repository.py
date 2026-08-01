from typing import Protocol

from tdp.modules.features.domain.model import (
    Feature,
    FeatureDocumentationMapItem,
    FeatureId,
    FeatureKey,
)


class FeatureRepository(Protocol):
    async def add(
        self,
        feature: Feature,
        documentation_map: list[FeatureDocumentationMapItem],
    ) -> None: ...

    async def update(self, feature: Feature) -> None: ...

    async def get(self, feature_id: FeatureId) -> Feature | None: ...

    async def get_by_project_key(
        self,
        project_id: str,
        key: FeatureKey,
    ) -> Feature | None: ...

    async def list_by_project(self, project_id: str) -> list[Feature]: ...

    async def list_documentation_map(
        self,
        feature_id: FeatureId,
    ) -> list[FeatureDocumentationMapItem]: ...
