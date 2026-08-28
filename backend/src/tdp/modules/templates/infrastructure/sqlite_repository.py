import sqlite3
from datetime import datetime

from tdp.modules.templates.domain.model import (
    DocumentTemplate,
    TemplateCategory,
    TemplateId,
    TemplateStandard,
)
from tdp.modules.templates.domain.repository import TemplateRepository


class SqliteTemplateRepository(TemplateRepository):
    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        self._ensure_schema()

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _ensure_schema(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS document_templates (
                    id TEXT PRIMARY KEY,
                    key TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT "",
                    category TEXT NOT NULL,
                    standard TEXT NOT NULL,
                    content TEXT NOT NULL,
                    is_builtin INTEGER NOT NULL DEFAULT 0,
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_templates_key ON document_templates(key)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_templates_category ON document_templates(category)"
            )

    async def get(self, template_id: TemplateId) -> DocumentTemplate | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM document_templates WHERE id = ?",
                (str(template_id),),
            ).fetchone()
            return _row_to_template(row) if row else None

    async def get_by_key(self, key: str) -> DocumentTemplate | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM document_templates WHERE key = ?",
                (key.upper(),),
            ).fetchone()
            return _row_to_template(row) if row else None

    async def list_all(self) -> list[DocumentTemplate]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM document_templates ORDER BY category, name"
            ).fetchall()
            return [_row_to_template(row) for row in rows]

    async def list_by_category(self, category: TemplateCategory) -> list[DocumentTemplate]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM document_templates WHERE category = ? ORDER BY name",
                (category.value,),
            ).fetchall()
            return [_row_to_template(row) for row in rows]

    async def add(self, template: DocumentTemplate) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO document_templates
                    (id, key, name, description, category, standard, content, is_builtin, version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _template_to_row(template),
            )

    async def update(self, template: DocumentTemplate) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                UPDATE document_templates
                SET name = ?, description = ?, content = ?, version = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    template.name,
                    template.description,
                    template.content,
                    template.version,
                    template.updated_at.isoformat(),
                    str(template.id),
                ),
            )

    async def delete(self, template_id: TemplateId) -> None:
        with self._connection() as connection:
            connection.execute(
                "DELETE FROM document_templates WHERE id = ?",
                (str(template_id),),
            )


def _row_to_template(row: sqlite3.Row) -> DocumentTemplate:
    return DocumentTemplate(
        id=TemplateId.from_string(row["id"]),
        key=row["key"],
        name=row["name"],
        description=row["description"],
        category=TemplateCategory(row["category"]),
        standard=TemplateStandard(row["standard"]),
        content=row["content"],
        is_builtin=bool(row["is_builtin"]),
        version=row["version"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _template_to_row(template: DocumentTemplate) -> tuple:
    return (
        str(template.id),
        template.key,
        template.name,
        template.description,
        template.category.value,
        template.standard.value,
        template.content,
        int(template.is_builtin),
        template.version,
        template.created_at.isoformat(),
        template.updated_at.isoformat(),
    )
