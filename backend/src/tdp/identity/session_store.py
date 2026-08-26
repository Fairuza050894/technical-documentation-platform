"""Token blacklist store for session invalidation.

Stores revoked token JTIs so they can be rejected
even before their natural expiry.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


class TokenBlacklist:
    """SQLite-backed token blacklist for logout / invalidation."""

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
                CREATE TABLE IF NOT EXISTS token_blacklist (
                    jti TEXT PRIMARY KEY,
                    revoked_at TEXT NOT NULL DEFAULT (datetime('now')),
                    expires_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_blacklist_expires
                ON token_blacklist (expires_at)
            """)
            conn.commit()

    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token JTI is blacklisted."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM token_blacklist WHERE jti = ?", (jti,)
            ).fetchone()
            return row is not None

    def add(self, jti: str, expires_at: str) -> None:
        """Add a token JTI to the blacklist."""
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO token_blacklist (jti, expires_at) VALUES (?, ?)",
                (jti, expires_at),
            )
            conn.commit()

    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns number of rows deleted."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM token_blacklist WHERE expires_at < datetime('now')"
            )
            conn.commit()
            return cursor.rowcount