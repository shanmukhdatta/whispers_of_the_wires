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
