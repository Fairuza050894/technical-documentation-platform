from typing import Protocol

from tdp.modules.catalog.domain.model import (
    ApiOperation,
    ApiSchema,
    SynchronizationId,
    SynchronizationRun,
)


class CatalogRepository(Protocol):
    async def add_run(self, run: SynchronizationRun) -> None: ...

    async def complete_run(
        self,
        run: SynchronizationRun,
        operations: list[ApiOperation],
        schemas: list[ApiSchema],
    ) -> None: ...

    async def update_run(self, run: SynchronizationRun) -> None: ...

    async def get_run(self, run_id: SynchronizationId) -> SynchronizationRun | None: ...

    async def list_runs_by_source(self, source_id: str) -> list[SynchronizationRun]: ...

    async def list_latest_runs(
        self,
        project_id: str,
        source_id: str | None = None,
    ) -> list[SynchronizationRun]: ...

    async def list_current_operations(
        self,
        project_id: str,
        source_id: str | None = None,
    ) -> list[ApiOperation]: ...

    async def list_current_schemas(
        self,
        project_id: str,
        source_id: str | None = None,
    ) -> list[ApiSchema]: ...
