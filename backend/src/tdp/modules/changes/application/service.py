from tdp.modules.catalog.domain.model import SynchronizationId, SynchronizationStatus
from tdp.modules.catalog.domain.repository import CatalogRepository
from tdp.modules.changes.application.dto import ComparisonDto
from tdp.modules.changes.domain.errors import ComparisonRunNotFoundError, InvalidComparisonError
from tdp.modules.changes.domain.model import DeterministicCatalogComparator


class ChangeDetectionApplicationService:
    def __init__(
        self,
        repository: CatalogRepository,
        comparator: DeterministicCatalogComparator,
    ) -> None:
        self._repository = repository
        self._comparator = comparator

    async def compare(
        self,
        project_id: str,
        baseline_run_id: str,
        target_run_id: str,
    ) -> ComparisonDto:
        if baseline_run_id == target_run_id:
            raise InvalidComparisonError("Baseline and target synchronization must be different.")

        baseline = await self._repository.get_run(SynchronizationId.from_string(baseline_run_id))
        target = await self._repository.get_run(SynchronizationId.from_string(target_run_id))
        if baseline is None or target is None:
            raise ComparisonRunNotFoundError("One or both synchronization runs were not found.")
        if baseline.project_id != project_id or target.project_id != project_id:
            raise InvalidComparisonError("Both synchronization runs must belong to the project.")
        if (
            baseline.status is not SynchronizationStatus.COMPLETED
            or target.status is not SynchronizationStatus.COMPLETED
        ):
            raise InvalidComparisonError("Only completed synchronization runs can be compared.")

        comparison = self._comparator.compare(
            project_id=project_id,
            baseline_run_id=baseline_run_id,
            target_run_id=target_run_id,
            baseline_operations=await self._repository.list_operations_by_run(baseline.id),
            target_operations=await self._repository.list_operations_by_run(target.id),
            baseline_schemas=await self._repository.list_schemas_by_run(baseline.id),
            target_schemas=await self._repository.list_schemas_by_run(target.id),
        )
        return ComparisonDto.from_domain(comparison)
