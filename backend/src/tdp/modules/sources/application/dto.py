from dataclasses import dataclass

from tdp.modules.sources.domain.model import SourceConnection


@dataclass(frozen=True, slots=True)
class SourceDto:
    id: str
    project_id: str
    name: str
    source_type: str
    status: str
    original_file_name: str
    media_type: str
    checksum: str
    openapi_version: str
    api_title: str
    api_version: str
    path_count: int
    operation_count: int
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(cls, source: SourceConnection) -> "SourceDto":
        return cls(
            id=str(source.id),
            project_id=str(source.project_id),
            name=str(source.name),
            source_type=source.source_type.value,
            status=source.status.value,
            original_file_name=str(source.original_file_name),
            media_type=source.media_type.value,
            checksum=str(source.checksum),
            openapi_version=source.openapi_version,
            api_title=source.api_title,
            api_version=source.api_version,
            path_count=source.path_count,
            operation_count=source.operation_count,
            created_at=source.created_at.isoformat(),
            updated_at=source.updated_at.isoformat(),
        )
