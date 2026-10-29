"""Single-user SQLite job persistence; durable across application restarts."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class JobStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root / "jobs.sqlite3"
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS jobs ("
                "id TEXT PRIMARY KEY, state TEXT NOT NULL, "
                "provider TEXT NOT NULL, request_id TEXT NOT NULL, "
                "data TEXT NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS favorites ("
                "job_id TEXT PRIMARY KEY, added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database)

    def save(self, job_id: str, *, state: str, provider: str,
             request_id: str, data: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO jobs (id,state,provider,request_id,data) VALUES(?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET state=excluded.state, data=excluded.data",
                (job_id, state, provider, request_id, json.dumps(data)),
            )

    def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        """Most recently created jobs, persisted for the Streamlit library."""
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id FROM jobs ORDER BY rowid DESC LIMIT ?", (limit,)
            ).fetchall()
        return [job for (job_id,) in rows if (job := self.get(job_id)) is not None]

    def favorites(self) -> set[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT job_id FROM favorites").fetchall()
        return {row[0] for row in rows}

    def set_favorite(self, job_id: str, favorite: bool) -> None:
        if self.get(job_id) is None:
            raise KeyError("Unknown composition")
        with self._connect() as conn:
            if favorite:
                conn.execute("INSERT OR IGNORE INTO favorites(job_id) VALUES(?)", (job_id,))
            else:
                conn.execute("DELETE FROM favorites WHERE job_id=?", (job_id,))

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id,state,provider,request_id,data FROM jobs WHERE id=?",
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return {"job_id": row[0], "state": row[1], "provider": row[2],
                "request_id": row[3], "data": json.loads(row[4])}
