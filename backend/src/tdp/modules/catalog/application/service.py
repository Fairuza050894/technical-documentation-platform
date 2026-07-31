import hashlib

from tdp.modules.catalog.application.dto import (
    ApiOperationDto,
    ApiSchemaDto,
    CatalogDto,
    SynchronizationDto,
)
from tdp.modules.catalog.application.ports import (
    ArtifactReader,
    OpenApiCatalogParser,
    ProjectCatalogAccess,
)
from tdp.modules.catalog.domain.errors import (
    CatalogArtifactIntegrityError,
    CatalogArtifactNotFoundError,
    CatalogError,
    CatalogProjectArchivedError,
    CatalogProjectNotFoundError,
    CatalogSourceArchivedError,
    CatalogSourceNotFoundError,
    SynchronizationNotFoundError,
)
from tdp.modules.catalog.domain.model import (
    ApiOperation,
    ApiSchema,
    SynchronizationId,
    SynchronizationRun,
)
from tdp.modules.catalog.domain.repository import CatalogRepository
from tdp.modules.sources.domain.model import SourceId, SourceStatus
from tdp.modules.sources.domain.repository import SourceRepository


class CatalogApplicationService:
    def __init__(
        self,
        catalog_repository: CatalogRepository,
        source_repository: SourceRepository,
        project_access: ProjectCatalogAccess,
        artifact_reader: ArtifactReader,
        parser: OpenApiCatalogParser,
    ) -> None:
        self._catalog_repository = catalog_repository
        self._source_repository = source_repository
        self._project_access = project_access
        self._artifact_reader = artifact_reader
        self._parser = parser

    async def synchronize(self, source_id: str) -> SynchronizationDto:
        source = await self._source_repository.get(SourceId.from_string(source_id))
        if source is None:
            raise CatalogSourceNotFoundError(f"Source {source_id} was not found.")
        if source.status is SourceStatus.ARCHIVED:
            raise CatalogSourceArchivedError(f"Source {source_id} is archived.")
        if not await self._project_access.is_active(str(source.project_id)):
            raise CatalogProjectArchivedError(
                "New synchronizations cannot be created for an archived project or workspace."
            )

        run = SynchronizationRun.start(
            project_id=str(source.project_id),
            source_id=str(source.id),
            source_checksum=str(source.checksum),
        )
        await self._catalog_repository.add_run(run)

        try:
            content = await self._artifact_reader.read(str(source.artifact_key))
            if hashlib.sha256(content).hexdigest() != run.source_checksum:
                raise CatalogArtifactIntegrityError(
                    "The stored artifact checksum does not match the source record."
                )
            parsed = self._parser.parse(content)
            operations = [
                ApiOperation(
                    synchronization_id=run.id,
                    project_id=run.project_id,
                    source_id=run.source_id,
                    method=item.method,
                    path=item.path,
                    operation_id=item.operation_id,
                    summary=item.summary,
                    description=item.description,
                    tags=item.tags,
                    deprecated=item.deprecated,
                    security_schemes=item.security_schemes,
                    parameters=item.parameters,
                    request_body=item.request_body,
                    responses=item.responses,
                    source_pointer=item.source_pointer,
                )
                for item in parsed.operations
            ]
            schemas = [
                ApiSchema(
                    synchronization_id=run.id,
                    project_id=run.project_id,
                    source_id=run.source_id,
                    name=item.name,
                    schema_type=item.schema_type,
                    description=item.description,
                    required_fields=item.required_fields,
                    properties=item.properties,
                    source_pointer=item.source_pointer,
                )
                for item in parsed.schemas
            ]
            run.complete(operation_count=len(operations), schema_count=len(schemas))
            await self._catalog_repository.complete_run(run, operations, schemas)
        except FileNotFoundError as exc:
            run.fail(
                error_code=CatalogArtifactNotFoundError.code,
                error_message="The source artifact could not be found.",
            )
            await self._catalog_repository.update_run(run)
            raise CatalogArtifactNotFoundError("The source artifact could not be found.") from exc
        except CatalogError as exc:
            run.fail(error_code=exc.code, error_message=str(exc))
            await self._catalog_repository.update_run(run)
            raise
        except Exception:
            run.fail(
                error_code="SYNCHRONIZATION_FAILED",
                error_message="The source could not be synchronized.",
            )
            await self._catalog_repository.update_run(run)
            raise

        return SynchronizationDto.from_domain(run)

    async def get_run(self, run_id: str) -> SynchronizationDto:
        run = await self._catalog_repository.get_run(SynchronizationId.from_string(run_id))
        if run is None:
            raise SynchronizationNotFoundError(f"Synchronization {run_id} was not found.")
        return SynchronizationDto.from_domain(run)

    async def list_runs(self, source_id: str) -> list[SynchronizationDto]:
        source = await self._source_repository.get(SourceId.from_string(source_id))
        if source is None:
            raise CatalogSourceNotFoundError(f"Source {source_id} was not found.")
        runs = await self._catalog_repository.list_runs_by_source(source_id)
        return [SynchronizationDto.from_domain(run) for run in runs]

    async def get_catalog(
        self,
        project_id: str,
        *,
        source_id: str | None = None,
    ) -> CatalogDto:
        if not await self._project_access.exists(project_id):
            raise CatalogProjectNotFoundError(f"Project {project_id} was not found.")

        normalized_source_id: str | None = None
        if source_id is not None:
            source = await self._source_repository.get(SourceId.from_string(source_id))
            if source is None or str(source.project_id) != project_id:
                raise CatalogSourceNotFoundError(
                    f"Source {source_id} was not found for project {project_id}."
                )
            normalized_source_id = str(source.id)

        runs = await self._catalog_repository.list_latest_runs(
            project_id,
            normalized_source_id,
        )
        operations = await self._catalog_repository.list_current_operations(
            project_id,
            normalized_source_id,
        )
        schemas = await self._catalog_repository.list_current_schemas(
            project_id,
            normalized_source_id,
        )
        return CatalogDto(
            runs=[SynchronizationDto.from_domain(run) for run in runs],
            operations=[ApiOperationDto.from_domain(operation) for operation in operations],
            schemas=[ApiSchemaDto.from_domain(schema) for schema in schemas],
        )
