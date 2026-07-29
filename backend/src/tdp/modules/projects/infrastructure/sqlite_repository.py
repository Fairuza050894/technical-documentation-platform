import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

from tdp.modules.projects.domain.errors import ProjectKeyAlreadyExistsError
from tdp.modules.projects.domain.model import (
    Project,
    ProjectDescription,
    ProjectId,
    ProjectKey,
    ProjectName,
    ProjectStatus,
    WorkspaceType,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    project_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    workspace_type TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class SqliteProjectRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    async def add(self, project: Project) -> None:
        try:
            await asyncio.to_thread(self._add, project)
        except sqlite3.IntegrityError as exc:
            raise ProjectKeyAlreadyExistsError(
                f"Project key {project.key} is already in use."
            ) from exc

    async def update(self, project: Project) -> None:
        await asyncio.to_thread(self._update, project)

    async def get(self, project_id: ProjectId) -> Project | None:
        return await asyncio.to_thread(self._get, project_id)

    async def get_by_key(self, key: ProjectKey) -> Project | None:
        return await asyncio.to_thread(self._get_by_key, key)

    async def list_all(self) -> list[Project]:
        return await asyncio.to_thread(self._list_all)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(_SCHEMA)

    def _add(self, project: Project) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO projects (
                    id, project_key, name, description, workspace_type,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_record(project),
            )

    def _update(self, project: Project) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE projects
                SET project_key = ?, name = ?, description = ?, workspace_type = ?,
                    status = ?, created_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    str(project.key),
                    str(project.name),
                    str(project.description),
                    project.workspace_type.value,
                    project.status.value,
                    project.created_at.isoformat(),
                    project.updated_at.isoformat(),
                    str(project.id),
                ),
            )

    def _get(self, project_id: ProjectId) -> Project | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM projects WHERE id = ?",
                (str(project_id),),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def _get_by_key(self, key: ProjectKey) -> Project | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM projects WHERE project_key = ?",
                (str(key),),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def _list_all(self) -> list[Project]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM projects ORDER BY created_at DESC, id ASC"
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _to_record(project: Project) -> tuple[str, str, str, str, str, str, str, str]:
        return (
            str(project.id),
            str(project.key),
            str(project.name),
            str(project.description),
            project.workspace_type.value,
            project.status.value,
            project.created_at.isoformat(),
            project.updated_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Project:
        return Project(
            id=ProjectId.from_string(str(row["id"])),
            key=ProjectKey(str(row["project_key"])),
            name=ProjectName(str(row["name"])),
            description=ProjectDescription(str(row["description"])),
            workspace_type=WorkspaceType(str(row["workspace_type"])),
            status=ProjectStatus(str(row["status"])),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )
