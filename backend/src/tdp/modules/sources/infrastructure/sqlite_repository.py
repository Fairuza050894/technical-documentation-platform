import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

from tdp.modules.sources.domain.errors import SourceNameAlreadyExistsError
from tdp.modules.sources.domain.model import (
    ArtifactKey,
    SourceChecksum,
    SourceConnection,
    SourceFileName,
    SourceId,
    SourceMediaType,
    SourceName,
    SourceProjectId,
    SourceStatus,
    SourceType,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    name_key TEXT NOT NULL,
    source_type TEXT NOT NULL,
    status TEXT NOT NULL,
    original_file_name TEXT NOT NULL,
    media_type TEXT NOT NULL,
    checksum TEXT NOT NULL,
    artifact_key TEXT NOT NULL UNIQUE,
    openapi_version TEXT NOT NULL,
    api_title TEXT NOT NULL,
    api_version TEXT NOT NULL,
    path_count INTEGER NOT NULL,
    operation_count INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    UNIQUE(project_id, name_key)
);
CREATE INDEX IF NOT EXISTS idx_sources_project_created
ON sources(project_id, created_at DESC);
"""


class SqliteSourceRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    async def add(self, source: SourceConnection) -> None:
        try:
            await asyncio.to_thread(self._add, source)
        except sqlite3.IntegrityError as exc:
            raise SourceNameAlreadyExistsError(
                f"Source name {source.name} is already in use for this project."
            ) from exc

    async def update(self, source: SourceConnection) -> None:
        await asyncio.to_thread(self._update, source)

    async def get(self, source_id: SourceId) -> SourceConnection | None:
        return await asyncio.to_thread(self._get, source_id)

    async def get_by_name(
        self,
        project_id: SourceProjectId,
        name: SourceName,
    ) -> SourceConnection | None:
        return await asyncio.to_thread(self._get_by_name, project_id, name)

    async def list_by_project(self, project_id: SourceProjectId) -> list[SourceConnection]:
        return await asyncio.to_thread(self._list_by_project, project_id)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(_SCHEMA)

    def _add(self, source: SourceConnection) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sources (
                    id, project_id, name, name_key, source_type, status,
                    original_file_name, media_type, checksum, artifact_key,
                    openapi_version, api_title, api_version, path_count,
                    operation_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_record(source),
            )

    def _update(self, source: SourceConnection) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE sources
                SET name = ?, name_key = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    str(source.name),
                    source.name.comparison_key,
                    source.status.value,
                    source.updated_at.isoformat(),
                    str(source.id),
                ),
            )

    def _get(self, source_id: SourceId) -> SourceConnection | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM sources WHERE id = ?",
                (str(source_id),),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def _get_by_name(
        self,
        project_id: SourceProjectId,
        name: SourceName,
    ) -> SourceConnection | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM sources WHERE project_id = ? AND name_key = ?",
                (str(project_id), name.comparison_key),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def _list_by_project(self, project_id: SourceProjectId) -> list[SourceConnection]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM sources
                WHERE project_id = ?
                ORDER BY created_at DESC, id ASC
                """,
                (str(project_id),),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _to_record(source: SourceConnection) -> tuple[object, ...]:
        return (
            str(source.id),
            str(source.project_id),
            str(source.name),
            source.name.comparison_key,
            source.source_type.value,
            source.status.value,
            str(source.original_file_name),
            source.media_type.value,
            str(source.checksum),
            str(source.artifact_key),
            source.openapi_version,
            source.api_title,
            source.api_version,
            source.path_count,
            source.operation_count,
            source.created_at.isoformat(),
            source.updated_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> SourceConnection:
        return SourceConnection(
            id=SourceId.from_string(str(row["id"])),
            project_id=SourceProjectId.from_string(str(row["project_id"])),
            name=SourceName(str(row["name"])),
            source_type=SourceType(str(row["source_type"])),
            status=SourceStatus(str(row["status"])),
            original_file_name=SourceFileName(str(row["original_file_name"])),
            media_type=SourceMediaType(str(row["media_type"])),
            checksum=SourceChecksum(str(row["checksum"])),
            artifact_key=ArtifactKey(str(row["artifact_key"])),
            openapi_version=str(row["openapi_version"]),
            api_title=str(row["api_title"]),
            api_version=str(row["api_version"]),
            path_count=int(row["path_count"]),
            operation_count=int(row["operation_count"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )
