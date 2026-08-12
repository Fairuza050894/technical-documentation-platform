import asyncio
import sqlite3
from pathlib import Path
from uuid import uuid4

from tdp.modules.documents.domain.model import DocumentVersionId
from tdp.modules.documents.infrastructure.sqlite_repository import SqliteDocumentRepository


def _create_legacy_database(database_path: Path) -> tuple[str, str]:
    document_id = str(uuid4())
    version_id = str(uuid4())
    event_id = str(uuid4())
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE documents (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                document_type TEXT NOT NULL,
                title TEXT NOT NULL,
                current_version_id TEXT,
                current_approved_version_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(project_id, document_type)
            );
            CREATE TABLE document_versions (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                target_run_id TEXT NOT NULL,
                baseline_run_id TEXT,
                document_type TEXT NOT NULL,
                document_format TEXT NOT NULL,
                version_major INTEGER NOT NULL,
                version_minor INTEGER NOT NULL,
                status TEXT NOT NULL,
                title TEXT NOT NULL,
                file_name TEXT NOT NULL,
                content TEXT NOT NULL,
                checksum TEXT NOT NULL,
                operation_count INTEGER NOT NULL,
                schema_count INTEGER NOT NULL,
                breaking_change_count INTEGER NOT NULL,
                revision_reason TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                submitted_at TEXT,
                approved_at TEXT,
                superseded_at TEXT,
                UNIQUE(document_id, version_major, version_minor),
                UNIQUE(document_id, checksum)
            );
            CREATE TABLE document_workflow_events (
                id TEXT PRIMARY KEY,
                version_id TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                previous_status TEXT,
                new_status TEXT NOT NULL,
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(version_id) REFERENCES document_versions(id)
            );
            """
        )
        created_at = "2026-08-11T10:00:00+00:00"
        connection.execute(
            """
            INSERT INTO documents (
                id, project_id, document_type, title, current_version_id,
                current_approved_version_id, created_at, updated_at
            ) VALUES (?, 'project-1', 'LLD', 'Low Level Design', ?, NULL, ?, ?)
            """,
            (document_id, version_id, created_at, created_at),
        )
        connection.execute(
            """
            INSERT INTO document_versions (
                id, document_id, project_id, source_id, target_run_id,
                baseline_run_id, document_type, document_format,
                version_major, version_minor, status, title, file_name,
                content, checksum, operation_count, schema_count,
                breaking_change_count, revision_reason, created_by,
                created_at, updated_at, submitted_at, approved_at, superseded_at
            ) VALUES (
                ?, ?, 'project-1', 'source-1', 'run-1', NULL, 'LLD', 'MARKDOWN',
                1, 0, 'DRAFT', 'Low Level Design', 'lld-v1.0.md', '# LLD\n', ?,
                1, 1, 0, 'Legacy version.', 'Technical Writer', ?, ?, NULL, NULL, NULL
            )
            """,
            (version_id, document_id, "a" * 64, created_at, created_at),
        )
        connection.execute(
            """
            INSERT INTO document_workflow_events (
                id, version_id, actor, action, previous_status,
                new_status, comment, created_at
            ) VALUES (?, ?, 'Technical Writer', 'GENERATED', NULL, 'DRAFT', 'Legacy version.', ?)
            """,
            (event_id, version_id, created_at),
        )
    return version_id, event_id


def test_repository_migrates_target_snapshot_to_nullable_without_losing_history(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "legacy-documents.sqlite3"
    version_id, event_id = _create_legacy_database(database_path)

    repository = SqliteDocumentRepository(database_path)

    version = asyncio.run(repository.get_version(DocumentVersionId.from_string(version_id)))
    assert version is not None
    assert version.target_run_id == "run-1"

    events = asyncio.run(repository.list_workflow_events(version.id))
    assert [str(event.id) for event in events] == [event_id]

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        columns = {
            str(row["name"]): row
            for row in connection.execute("PRAGMA table_info(document_versions)").fetchall()
        }
        assert int(columns["target_run_id"]["notnull"]) == 0

        workflow_foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(document_workflow_events)"
        ).fetchall()
        assert any(str(row["table"]) == "document_versions" for row in workflow_foreign_keys)
