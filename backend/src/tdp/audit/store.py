"""SQLite-backed audit event store.

Provides persistent, queryable storage for audit events
complementing the structlog-based StructuredAuditLogger.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from tdp.audit.model import AuditEvent


class AuditStore:
    """Append-only SQLite store for audit events."""

    def __init__(self, database_path: Path) -> None:
        self._db_path = database_path
        self._ensure_table()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _ensure_table(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    actor_display_name TEXT NOT NULL DEFAULT '',
                    action TEXT NOT NULL,
                    resource_type TEXT NOT NULL DEFAULT '',
                    resource_id TEXT,
                    workspace_id TEXT,
                    project_id TEXT,
                    request_id TEXT,
                    ip_address TEXT NOT NULL DEFAULT '',
                    success INTEGER NOT NULL DEFAULT 1,
                    error_message TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_ts
                ON audit_logs (timestamp DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_actor
                ON audit_logs (actor_id, timestamp DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_action
                ON audit_logs (action, timestamp DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_resource
                ON audit_logs (resource_type, resource_id, timestamp DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_workspace
                ON audit_logs (workspace_id, timestamp DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_project
                ON audit_logs (project_id, timestamp DESC)
            """)
            conn.commit()

    def insert(self, event: AuditEvent) -> None:
        """Persist a single audit event to SQLite."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (
                    event_id, timestamp, actor_id, actor_display_name,
                    action, resource_type, resource_id,
                    workspace_id, project_id, request_id,
                    ip_address, success, error_message, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.timestamp.isoformat(),
                    event.actor_id,
                    event.actor_display_name,
                    event.action.value,
                    event.resource_type,
                    event.resource_id,
                    event.workspace_id,
                    event.project_id,
                    event.request_id,
                    event.ip_address,
                    1 if event.success else 0,
                    event.error_message,
                    json.dumps(event.metadata) if event.metadata else None,
                ),
            )
            conn.commit()

    def query(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        actor_id: str | None = None,
        actions: list[str] | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        workspace_id: str | None = None,
        project_id: str | None = None,
        success: bool | None = None,
        request_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """Query audit logs with filtering, pagination, and sorting."""
        conditions: list[str] = []
        params: list[Any] = []

        if actor_id:
            conditions.append("actor_id = ?")
            params.append(actor_id)
        if actions:
            placeholders = ",".join("?" for _ in actions)
            conditions.append(f"action IN ({placeholders})")
            params.extend(actions)
        if resource_type:
            conditions.append("resource_type LIKE ?")
            params.append(f"%{resource_type}%")
        if resource_id:
            conditions.append("resource_id = ?")
            params.append(resource_id)
        if workspace_id:
            conditions.append("workspace_id = ?")
            params.append(workspace_id)
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if success is not None:
            conditions.append("success = ?")
            params.append(1 if success else 0)
        if request_id:
            conditions.append("request_id = ?")
            params.append(request_id)
        if start_date:
            conditions.append("timestamp >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("timestamp <= ?")
            params.append(end_date)
        if search:
            conditions.append(
                "(resource_type LIKE ? OR actor_id LIKE ? "
                "OR actor_display_name LIKE ? OR request_id LIKE ? "
                "OR error_message LIKE ?)"
            )
            pattern = f"%{search}%"
            params.extend([pattern] * 5)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        allowed_sort = {
            "timestamp", "action", "actor_id",
            "resource_type", "success", "created_at",
        }
        col = sort_by if sort_by in allowed_sort else "timestamp"
        direction = "ASC" if sort_order.lower() == "asc" else "DESC"

        safe_page = max(1, page)
        safe_size = min(max(1, page_size), 200)
        offset = (safe_page - 1) * safe_size

        with self._connect() as conn:
            count_row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM audit_logs {where}", params
            ).fetchone()
            total = count_row["cnt"]

            rows = conn.execute(
                f"SELECT * FROM audit_logs {where} "
                f"ORDER BY {col} {direction} LIMIT ? OFFSET ?",
                params + [safe_size, offset],
            ).fetchall()

        logs = []
        for row in rows:
            log = dict(row)
            if log.get("metadata"):
                log["metadata"] = json.loads(log["metadata"])
            log["success"] = bool(log["success"])
            logs.append(log)

        return {
            "logs": logs,
            "pagination": {
                "page": safe_page,
                "page_size": safe_size,
                "total": total,
                "total_pages": max(1, -(-total // safe_size)),
            },
        }

    def get_by_id(self, log_id: int) -> dict[str, Any] | None:
        """Get a single audit log by its auto-increment ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM audit_logs WHERE id = ?", (log_id,)
            ).fetchone()
        if not row:
            return None
        log = dict(row)
        if log.get("metadata"):
            log["metadata"] = json.loads(log["metadata"])
        log["success"] = bool(log["success"])
        return log

    def stats(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Aggregate statistics for audit logs."""
        conditions: list[str] = []
        params: list[Any] = []
        if start_date:
            conditions.append("timestamp >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("timestamp <= ?")
            params.append(end_date)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self._connect() as conn:
            by_action = [
                dict(r)
                for r in conn.execute(
                    f"SELECT action, COUNT(*) as count FROM audit_logs {where} "
                    "GROUP BY action ORDER BY count DESC",
                    params,
                ).fetchall()
            ]

            by_resource = [
                dict(r)
                for r in conn.execute(
                    f"SELECT resource_type, COUNT(*) as count FROM audit_logs {where} "
                    "GROUP BY resource_type ORDER BY count DESC LIMIT 10",
                    params,
                ).fetchall()
            ]

            by_outcome = [
                dict(r)
                for r in conn.execute(
                    f"SELECT success, COUNT(*) as count FROM audit_logs {where} "
                    "GROUP BY success",
                    params,
                ).fetchall()
            ]

            daily = [
                dict(r)
                for r in conn.execute(
                    """
                    SELECT DATE(timestamp) as date, COUNT(*) as count
                    FROM audit_logs
                    WHERE timestamp >= datetime('now', '-30 days')
                    GROUP BY DATE(timestamp)
                    ORDER BY date ASC
                    """,
                ).fetchall()
            ]

            top_actors = [
                dict(r)
                for r in conn.execute(
                    f"""
                    SELECT actor_id, actor_display_name,
                           COUNT(*) as count,
                           MAX(timestamp) as last_activity
                    FROM audit_logs {where}
                    GROUP BY actor_id
                    ORDER BY count DESC
                    LIMIT 10
                    """,
                    params,
                ).fetchall()
            ]

        return {
            "by_action": by_action,
            "by_resource": by_resource,
            "by_outcome": by_outcome,
            "daily_activity": daily,
            "top_actors": top_actors,
        }