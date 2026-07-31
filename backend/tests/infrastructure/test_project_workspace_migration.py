import asyncio
import sqlite3
from pathlib import Path

from tdp.modules.projects.domain.model import OwnershipType, ProjectKey
from tdp.modules.projects.infrastructure.sqlite_repository import SqliteProjectRepository
from tdp.modules.workspaces.domain.model import DEFAULT_WORKSPACE_ID


def test_legacy_projects_receive_default_workspace_and_ownership(tmp_path: Path) -> None:
    database_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE projects (
                id TEXT PRIMARY KEY,
                project_key TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                workspace_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            INSERT INTO projects (
                id, project_key, name, description, workspace_type,
                status, created_at, updated_at
            ) VALUES (
                '11111111-1111-4111-8111-111111111111',
                'ERP',
                'ERP Platform',
                '',
                'ENTERPRISE',
                'ACTIVE',
                '2026-07-30T00:00:00+00:00',
                '2026-07-30T00:00:00+00:00'
            );
            """
        )

    repository = SqliteProjectRepository(database_path)
    migrated = asyncio.run(repository.get_by_key(ProjectKey("ERP")))

    assert migrated is not None
    assert migrated.workspace_id == DEFAULT_WORKSPACE_ID
    assert migrated.ownership_type is OwnershipType.TEAM
