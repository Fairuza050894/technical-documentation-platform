import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

from tdp.modules.documents.domain.model import (
    DocumentFormat,
    DocumentId,
    DocumentType,
    GeneratedDocument,
)
from tdp.modules.documents.domain.repository import DocumentRepository

_SCHEMA = """
CREATE TABLE IF NOT EXISTS generated_documents (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    target_run_id TEXT NOT NULL,
    baseline_run_id TEXT,
    document_type TEXT NOT NULL,
    document_format TEXT NOT NULL,
    title TEXT NOT NULL,
    file_name TEXT NOT NULL,
    content TEXT NOT NULL,
    checksum TEXT NOT NULL,
    operation_count INTEGER NOT NULL,
    schema_count INTEGER NOT NULL,
    breaking_change_count INTEGER NOT NULL,
    generated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(source_id) REFERENCES sources(id),
    FOREIGN KEY(target_run_id) REFERENCES catalog_sync_runs(id),
    FOREIGN KEY(baseline_run_id) REFERENCES catalog_sync_runs(id)
);
CREATE INDEX IF NOT EXISTS idx_generated_documents_project_created
ON generated_documents(project_id, generated_at DESC, id DESC);
"""


class SqliteDocumentRepository(DocumentRepository):
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    async def add(self, document: GeneratedDocument) -> None:
        await asyncio.to_thread(self._add, document)

    async def get(self, document_id: DocumentId) -> GeneratedDocument | None:
        return await asyncio.to_thread(self._get, document_id)

    async def list_by_project(self, project_id: str) -> list[GeneratedDocument]:
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

    def _add(self, document: GeneratedDocument) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO generated_documents (
                    id, project_id, source_id, target_run_id, baseline_run_id,
                    document_type, document_format, title, file_name, content,
                    checksum, operation_count, schema_count, breaking_change_count,
                    generated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._record(document),
            )

    def _get(self, document_id: DocumentId) -> GeneratedDocument | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM generated_documents WHERE id = ?",
                (str(document_id),),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def _list_by_project(self, project_id: str) -> list[GeneratedDocument]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM generated_documents
                WHERE project_id = ?
                ORDER BY generated_at DESC, id DESC
                """,
                (project_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _record(document: GeneratedDocument) -> tuple[object, ...]:
        return (
            str(document.id),
            document.project_id,
            document.source_id,
            document.target_run_id,
            document.baseline_run_id,
            document.document_type.value,
            document.document_format.value,
            document.title,
            document.file_name,
            document.content,
            document.checksum,
            document.operation_count,
            document.schema_count,
            document.breaking_change_count,
            document.generated_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> GeneratedDocument:
        baseline_run_id = row["baseline_run_id"]
        return GeneratedDocument(
            id=DocumentId.from_string(str(row["id"])),
            project_id=str(row["project_id"]),
            source_id=str(row["source_id"]),
            target_run_id=str(row["target_run_id"]),
            baseline_run_id=str(baseline_run_id) if baseline_run_id is not None else None,
            document_type=DocumentType(str(row["document_type"])),
            document_format=DocumentFormat(str(row["document_format"])),
            title=str(row["title"]),
            file_name=str(row["file_name"]),
            content=str(row["content"]),
            checksum=str(row["checksum"]),
            operation_count=int(row["operation_count"]),
            schema_count=int(row["schema_count"]),
            breaking_change_count=int(row["breaking_change_count"]),
            generated_at=datetime.fromisoformat(str(row["generated_at"])),
        )
