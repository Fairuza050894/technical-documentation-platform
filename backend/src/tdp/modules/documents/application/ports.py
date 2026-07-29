from dataclasses import dataclass
from typing import Protocol

from tdp.modules.catalog.domain.model import ApiOperation, ApiSchema, SynchronizationRun
from tdp.modules.changes.domain.model import Comparison
from tdp.modules.projects.domain.model import Project
from tdp.modules.sources.domain.model import SourceConnection


@dataclass(frozen=True, slots=True)
class TechnicalSourceOverviewContext:
    project: Project
    source: SourceConnection
    target_run: SynchronizationRun
    operations: tuple[ApiOperation, ...]
    schemas: tuple[ApiSchema, ...]
    comparison: Comparison | None


class TechnicalSourceOverviewRenderer(Protocol):
    def render(self, context: TechnicalSourceOverviewContext) -> str: ...
