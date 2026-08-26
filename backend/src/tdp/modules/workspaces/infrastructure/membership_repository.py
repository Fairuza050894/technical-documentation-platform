"""SQLite-backed workspace membership repository."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from tdp.authorization.model import Role
from tdp.modules.workspaces.domain.membership import WorkspaceMember


class SqliteMembershipRepository:
    """Persists workspace membership in SQLite."""

    def __init__(self, database_path: Path) -> None:
        self._db_path = database_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_table()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _ensure_table(self) -> None:
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS workspace_members ("
                "workspace_id TEXT NOT NULL, "
                "subject_id TEXT NOT NULL, "
                "role TEXT NOT NULL, "
                "added_at TEXT NOT NULL, "
                "added_by TEXT NOT NULL, "
                "PRIMARY KEY (workspace_id, subject_id, role))"
            )
            conn.commit()

    def add_member(self, member: WorkspaceMember) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO workspace_members"
                " (workspace_id, subject_id, role, added_at, added_by)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    member.workspace_id,
                    member.subject_id,
                    member.role.value,
                    member.added_at.isoformat(),
                    member.added_by,
                ),
            )
            conn.commit()

    def remove_member(
        self, workspace_id: str, subject_id: str, role: Role
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM workspace_members"
                " WHERE workspace_id = ? AND subject_id = ? AND role = ?",
                (workspace_id, subject_id, role.value),
            )
            conn.commit()

    def get_roles(self, subject_id: str, workspace_id: str) -> frozenset[Role]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT role FROM workspace_members"
                " WHERE subject_id = ? AND workspace_id = ?",
                (subject_id, workspace_id),
            ).fetchall()
        return frozenset(Role(row["role"]) for row in rows)

    def list_members(self, workspace_id: str) -> list[WorkspaceMember]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM workspace_members"
                " WHERE workspace_id = ? ORDER BY added_at",
                (workspace_id,),
            ).fetchall()
        return [
            WorkspaceMember(
                workspace_id=row["workspace_id"],
                subject_id=row["subject_id"],
                role=Role(row["role"]),
                added_at=datetime.fromisoformat(row["added_at"]),
                added_by=row["added_by"],
            )
            for row in rows
        ]

    def list_workspaces_for_subject(self, subject_id: str) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT workspace_id FROM workspace_members"
                " WHERE subject_id = ?",
                (subject_id,),
            ).fetchall()
        return [row["workspace_id"] for row in rows]
