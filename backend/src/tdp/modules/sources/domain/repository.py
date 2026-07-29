from typing import Protocol

from tdp.modules.sources.domain.model import (
    SourceConnection,
    SourceId,
    SourceName,
    SourceProjectId,
)


class SourceRepository(Protocol):
    async def add(self, source: SourceConnection) -> None: ...

    async def update(self, source: SourceConnection) -> None: ...

    async def get(self, source_id: SourceId) -> SourceConnection | None: ...

    async def get_by_name(
        self,
        project_id: SourceProjectId,
        name: SourceName,
    ) -> SourceConnection | None: ...

    async def list_by_project(self, project_id: SourceProjectId) -> list[SourceConnection]: ...
