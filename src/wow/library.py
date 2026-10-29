"""Local single-user composition library, favorites, playlists, and preferences."""
from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any


class LibraryStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.file = self.root / "library.sqlite3"
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS favorites (composition_id TEXT PRIMARY KEY)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS playlists("
                "id TEXT PRIMARY KEY, name TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS playlist_items("
                "playlist_id TEXT NOT NULL, composition_id TEXT NOT NULL,"
                "PRIMARY KEY(playlist_id, composition_id))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS settings("
                "name TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.file)

    def favorite(self, composition_id: str, active: bool) -> dict:
        with self._connect() as db:
            if active:
                db.execute(
                    "INSERT OR IGNORE INTO favorites(composition_id) VALUES(?)",
                    (composition_id,),
                )
            else:
                db.execute(
                    "DELETE FROM favorites WHERE composition_id=?", (composition_id,)
                )
        return {"composition_id": composition_id, "favorite": active}

    def favorites(self) -> set[str]:
        with self._connect() as db:
            rows = db.execute("SELECT composition_id FROM favorites").fetchall()
        return {row[0] for row in rows}

    def create_playlist(self, name: str) -> dict:
        name = name.strip()
        if not 1 <= len(name) <= 80:
            raise ValueError("Playlist name must be between 1 and 80 characters")
        playlist_id = str(uuid.uuid4())
        with self._connect() as db:
            db.execute(
                "INSERT INTO playlists(id, name) VALUES(?, ?)", (playlist_id, name)
            )
        return {"id": playlist_id, "name": name, "items": []}

    def playlists(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            lists = db.execute("SELECT id,name FROM playlists ORDER BY rowid DESC").fetchall()
            rows = db.execute(
                "SELECT playlist_id, composition_id FROM playlist_items ORDER BY rowid"
            ).fetchall()
        songs: dict[str, list[str]] = {}
        for playlist_id, composition_id in rows:
            songs.setdefault(playlist_id, []).append(composition_id)
        return [{"id": item[0], "name": item[1], "items": songs.get(item[0], [])}
                for item in lists]

    def add_item(self, playlist_id: str, composition_id: str) -> None:
        with self._connect() as db:
            if not db.execute(
                "SELECT 1 FROM playlists WHERE id=?", (playlist_id,)
            ).fetchone():
                raise KeyError("Unknown playlist")
            db.execute(
                "INSERT OR IGNORE INTO playlist_items(playlist_id,composition_id)"
                "VALUES(?,?)", (playlist_id, composition_id)
            )

    def remove_item(self, playlist_id: str, composition_id: str) -> None:
        with self._connect() as db:
            if not db.execute(
                "SELECT 1 FROM playlists WHERE id=?", (playlist_id,)
            ).fetchone():
                raise KeyError("Unknown playlist")
            db.execute(
                "DELETE FROM playlist_items WHERE playlist_id=? AND composition_id=?",
                (playlist_id, composition_id),
            )

    def settings(self) -> dict[str, Any]:
        default = {"default_genre": "cinematic", "default_tempo": 96,
                   "listen_volume": 80, "default_provider": "rule_based"}
        with self._connect() as db:
            records = db.execute("SELECT name,value FROM settings").fetchall()
        default.update({key: json.loads(value) for key, value in records})
        return default

    def save_settings(self, settings: dict[str, Any]) -> dict:
        with self._connect() as db:
            for key, value in settings.items():
                db.execute(
                    "INSERT INTO settings(name,value) VALUES(?,?) "
                    "ON CONFLICT(name) DO UPDATE SET value=excluded.value",
                    (key, json.dumps(value)),
                )
        return self.settings()
