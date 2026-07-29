from tdp.modules.sources.application.commands import ImportOpenApiSourceCommand
from tdp.modules.sources.application.dto import SourceDto
from tdp.modules.sources.application.ports import (
    ArtifactStore,
    OpenApiInspector,
    ProjectAccessPort,
)
from tdp.modules.sources.domain.errors import (
    EmptySourceFileError,
    SourceFileTooLargeError,
    SourceNameAlreadyExistsError,
    SourceNotFoundError,
    SourceProjectArchivedError,
    SourceProjectNotFoundError,
)
from tdp.modules.sources.domain.model import (
    ArtifactKey,
    SourceChecksum,
    SourceConnection,
    SourceFileName,
    SourceId,
    SourceName,
    SourceProjectId,
)
from tdp.modules.sources.domain.repository import SourceRepository


class SourceApplicationService:
    def __init__(
        self,
        repository: SourceRepository,
        project_access: ProjectAccessPort,
        inspector: OpenApiInspector,
        artifact_store: ArtifactStore,
        *,
        max_file_bytes: int,
    ) -> None:
        self._repository = repository
        self._project_access = project_access
        self._inspector = inspector
        self._artifact_store = artifact_store
        self._max_file_bytes = max_file_bytes

    @property
    def max_file_bytes(self) -> int:
        return self._max_file_bytes

    async def import_openapi(self, command: ImportOpenApiSourceCommand) -> SourceDto:
        project_id = SourceProjectId.from_string(command.project_id)
        await self._require_project(str(project_id), require_active=True)

        name = SourceName(command.name)
        if await self._repository.get_by_name(project_id, name) is not None:
            raise SourceNameAlreadyExistsError(
                f"Source name {name} is already in use for this project."
            )

        if not command.content:
            raise EmptySourceFileError("OpenAPI source file must not be empty.")
        if len(command.content) > self._max_file_bytes:
            raise SourceFileTooLargeError(
                f"OpenAPI source file must not exceed {self._max_file_bytes} bytes."
            )

        file_name = SourceFileName(command.file_name)
        inspection = self._inspector.inspect(file_name, command.content)
        source_id = SourceId.new()
        stored_artifact = await self._artifact_store.save(source_id, file_name, command.content)

        source = SourceConnection.create_openapi_file(
            source_id=source_id,
            project_id=project_id,
            name=name,
            original_file_name=file_name,
            media_type=inspection.media_type,
            checksum=SourceChecksum(inspection.checksum),
            artifact_key=ArtifactKey(stored_artifact.key),
            openapi_version=inspection.openapi_version,
            api_title=inspection.api_title,
            api_version=inspection.api_version,
            path_count=inspection.path_count,
            operation_count=inspection.operation_count,
        )

        try:
            await self._repository.add(source)
        except Exception:
            await self._artifact_store.delete(stored_artifact.key)
            raise
        return SourceDto.from_domain(source)

    async def list_sources(self, project_id: str) -> list[SourceDto]:
        normalized_project_id = SourceProjectId.from_string(project_id)
        await self._require_project(str(normalized_project_id), require_active=False)
        sources = await self._repository.list_by_project(normalized_project_id)
        return [SourceDto.from_domain(source) for source in sources]

    async def get(self, source_id: str) -> SourceDto:
        source = await self._repository.get(SourceId.from_string(source_id))
        if source is None:
            raise SourceNotFoundError(f"Source {source_id} was not found.")
        return SourceDto.from_domain(source)

    async def archive(self, source_id: str) -> SourceDto:
        source = await self._repository.get(SourceId.from_string(source_id))
        if source is None:
            raise SourceNotFoundError(f"Source {source_id} was not found.")
        source.archive()
        await self._repository.update(source)
        return SourceDto.from_domain(source)

    async def _require_project(self, project_id: str, *, require_active: bool) -> None:
        if not await self._project_access.exists(project_id):
            raise SourceProjectNotFoundError(f"Project {project_id} was not found.")
        if require_active and not await self._project_access.is_active(project_id):
            raise SourceProjectArchivedError("New sources cannot be added to an archived project.")
