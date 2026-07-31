import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

from tdp.modules.workspaces.domain.errors import WorkspaceKeyAlreadyExistsError
from tdp.modules.workspaces.domain.model import (
    DEFAULT_WORKSPACE_ID,
    Workspace,
    WorkspaceDescription,
    WorkspaceId,
    WorkspaceKey,
    WorkspaceName,
    WorkspaceStatus,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    workspace_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_workspaces_status_created
ON workspaces(status, created_at DESC, id ASC);
"""


class SqliteWorkspaceRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    async def add(self, workspace: Workspace) -> None:
        try:
            await asyncio.to_thread(self._add, workspace)
        except sqlite3.IntegrityError as exc:
            raise WorkspaceKeyAlreadyExistsError(
                f"Workspace key {workspace.key} is already in use."
            ) from exc

    async def update(self, workspace: Workspace) -> None:
        await asyncio.to_thread(self._update, workspace)

    async def get(self, workspace_id: WorkspaceId) -> Workspace | None:
        return await asyncio.to_thread(self._get, workspace_id)

    async def get_by_key(self, key: WorkspaceKey) -> Workspace | None:
        return await asyncio.to_thread(self._get_by_key, key)

    async def list_all(self) -> list[Workspace]:
        return await asyncio.to_thread(self._list_all)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(_SCHEMA)
            default_workspace = Workspace.default()
            connection.execute(
                """
                INSERT OR IGNORE INTO workspaces (
                    id, workspace_key, name, description, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_record(default_workspace),
            )
            row = connection.execute(
                "SELECT id FROM workspaces WHERE workspace_key = ?",
                (str(default_workspace.key),),
            ).fetchone()
            if row is None or str(row["id"]) != DEFAULT_WORKSPACE_ID:
                raise RuntimeError("The default workspace key is assigned to another workspace.")

    def _add(self, workspace: Workspace) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO workspaces (
                    id, workspace_key, name, description, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_record(workspace),
            )

    def _update(self, workspace: Workspace) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE workspaces
                SET workspace_key = ?, name = ?, description = ?, status = ?,
                    created_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    str(workspace.key),
                    str(workspace.name),
                    str(workspace.description),
                    workspace.status.value,
                    workspace.created_at.isoformat(),
                    workspace.updated_at.isoformat(),
                    str(workspace.id),
                ),
            )

    def _get(self, workspace_id: WorkspaceId) -> Workspace | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM workspaces WHERE id = ?",
                (str(workspace_id),),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def _get_by_key(self, key: WorkspaceKey) -> Workspace | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM workspaces WHERE workspace_key = ?",
                (str(key),),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def _list_all(self) -> list[Workspace]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM workspaces
                ORDER BY CASE status WHEN 'ACTIVE' THEN 0 ELSE 1 END,
                         created_at ASC,
                         id ASC
                """
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _to_record(workspace: Workspace) -> tuple[str, str, str, str, str, str, str]:
        return (
            str(workspace.id),
            str(workspace.key),
            str(workspace.name),
            str(workspace.description),
            workspace.status.value,
            workspace.created_at.isoformat(),
            workspace.updated_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Workspace:
        return Workspace(
            id=WorkspaceId.from_string(str(row["id"])),
            key=WorkspaceKey(str(row["workspace_key"])),
            name=WorkspaceName(str(row["name"])),
            description=WorkspaceDescription(str(row["description"])),
            status=WorkspaceStatus(str(row["status"])),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )
