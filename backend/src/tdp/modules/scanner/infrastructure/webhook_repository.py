import json
import sqlite3
from datetime import datetime

from tdp.modules.scanner.domain.webhook import (
    WebhookEvent,
    WebhookEventId,
    WebhookEventType,
    WebhookStatus,
)
from tdp.modules.scanner.domain.webhook_repository import WebhookRepository


class SqliteWebhookRepository(WebhookRepository):
    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        self._ensure_schema()

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _ensure_schema(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS webhook_events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    repository_url TEXT NOT NULL,
                    repository_name TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    commit_sha TEXT NOT NULL,
                    commit_message TEXT NOT NULL DEFAULT '',
                    sender TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    scan_id TEXT NOT NULL DEFAULT '',
                    previous_scan_id TEXT NOT NULL DEFAULT '',
                    score_delta INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    processed_at TEXT
                )
                """
            )

    async def save(self, event: WebhookEvent) -> None:
        with self._connection() as connection:
            existing = connection.execute(
                "SELECT id FROM webhook_events WHERE id = ?", (str(event.id),)
            ).fetchone()

            if existing:
                connection.execute(
                    """UPDATE webhook_events SET status=?, scan_id=?, previous_scan_id=?,
                    score_delta=?, error_message=?, processed_at=? WHERE id=?""",
                    (
                        event.status.value, event.scan_id, event.previous_scan_id,
                        event.score_delta, event.error_message,
                        event.processed_at.isoformat() if event.processed_at else None,
                        str(event.id),
                    ),
                )
            else:
                connection.execute(
                    """INSERT INTO webhook_events
                    (id, event_type, repository_url, repository_name, branch, commit_sha,
                    commit_message, sender, status, scan_id, previous_scan_id, score_delta,
                    error_message, created_at, processed_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        str(event.id), event.event_type.value, event.repository_url,
                        event.repository_name, event.branch, event.commit_sha,
                        event.commit_message, event.sender, event.status.value,
                        event.scan_id, event.previous_scan_id, event.score_delta,
                        event.error_message, event.created_at.isoformat(),
                        event.processed_at.isoformat() if event.processed_at else None,
                    ),
                )

    async def get(self, event_id: WebhookEventId) -> WebhookEvent | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM webhook_events WHERE id = ?", (str(event_id),)
            ).fetchone()
            return _row_to_event(row) if row else None

    async def list_all(self, limit: int = 50) -> list[WebhookEvent]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM webhook_events ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [_row_to_event(row) for row in rows]

    async def list_by_repo(self, repository_url: str, limit: int = 20) -> list[WebhookEvent]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM webhook_events WHERE repository_url = ? ORDER BY created_at DESC LIMIT ?",
                (repository_url, limit),
            ).fetchall()
            return [_row_to_event(row) for row in rows]


def _row_to_event(row: sqlite3.Row) -> WebhookEvent:
    return WebhookEvent(
        id=WebhookEventId.from_string(row["id"]),
        event_type=WebhookEventType(row["event_type"]),
        repository_url=row["repository_url"],
        repository_name=row["repository_name"],
        branch=row["branch"],
        commit_sha=row["commit_sha"],
        commit_message=row["commit_message"],
        sender=row["sender"],
        status=WebhookStatus(row["status"]),
        scan_id=row["scan_id"],
        previous_scan_id=row["previous_scan_id"],
        score_delta=row["score_delta"],
        error_message=row["error_message"],
        created_at=datetime.fromisoformat(row["created_at"]),
        processed_at=datetime.fromisoformat(row["processed_at"]) if row["processed_at"] else None,
    )
