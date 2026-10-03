from typing import Protocol

from tdp.modules.requirements.domain.model import (
    RequirementId,
    RequirementKey,
    RequirementRevision,
    RequirementRevisionId,
    TraceLink,
)


class RequirementRepository(Protocol):
    async def add_revision(self, revision: RequirementRevision) -> None: ...

    async def get_latest(
        self,
        project_id: str,
        requirement_id: RequirementId,
    ) -> RequirementRevision | None: ...

    async def get_latest_by_key(
        self,
        project_id: str,
        key: RequirementKey,
    ) -> RequirementRevision | None: ...

    async def list_latest_by_project(self, project_id: str) -> list[RequirementRevision]: ...

    async def list_revisions(
        self,
        project_id: str,
        requirement_id: RequirementId,
    ) -> list[RequirementRevision]: ...

    async def add_trace_link(self, link: TraceLink) -> None: ...

    async def list_trace_links(
        self,
        requirement_revision_id: RequirementRevisionId,
    ) -> list[TraceLink]: ...
