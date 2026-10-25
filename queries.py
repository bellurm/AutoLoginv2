from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SiteRecord:
    id: int
    label: str
    url: str
    username: str
    password: str
    username_selector: str
    password_selector: str
    submit_selector: str


class Database:
    """SQLite repository used by AutoLoginv2."""

    _EXTRA_COLUMNS = {
        "label": "TEXT NOT NULL DEFAULT ''",
        "username_selector": "TEXT NOT NULL DEFAULT ''",
        "password_selector": "TEXT NOT NULL DEFAULT ''",
        "submit_selector": "TEXT NOT NULL DEFAULT ''",
    }

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(
            self.path,
            timeout=10,
        )
        connection.row_factory = sqlite3.Row
        connection.execute(
            "PRAGMA foreign_keys = ON"
        )
        connection.execute(
            "PRAGMA busy_timeout = 10000"
        )
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        """
        Create the database if necessary and upgrade the
        original AutoLoginv2 schema without deleting records.
        """

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS siteRecords (
                    url TEXT NOT NULL,
                    username TEXT NOT NULL,
                    passwd TEXT NOT NULL
                )
                """
            )

            existing_columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(siteRecords)"
                )
            }

            for name, definition in self._EXTRA_COLUMNS.items():
                if name not in existing_columns:
                    connection.execute(
                        f"""
                        ALTER TABLE siteRecords
                        ADD COLUMN {name} {definition}
                        """
                    )

    def list_records(self) -> list[SiteRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    rowid AS id,
                    label,
                    url,
                    username,
                    passwd,
                    username_selector,
                    password_selector,
                    submit_selector
                FROM siteRecords
                ORDER BY rowid DESC
                """
            ).fetchall()

        return [
            self._to_record(row)
            for row in rows
        ]

    def get_record(
        self,
        record_id: int,
    ) -> SiteRecord | None:

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    rowid AS id,
                    label,
                    url,
                    username,
                    passwd,
                    username_selector,
                    password_selector,
                    submit_selector
                FROM siteRecords
                WHERE rowid = ?
                """,
                (record_id,),
            ).fetchone()

        if row is None:
            return None

        return self._to_record(row)

    def add_record(
        self,
        *,
        label: str,
        encrypted_url: str,
        encrypted_username: str,
        encrypted_password: str,
        username_selector: str,
        password_selector: str,
        submit_selector: str,
    ) -> int:

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO siteRecords (
                    label,
                    url,
                    username,
                    passwd,
                    username_selector,
                    password_selector,
                    submit_selector
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    label,
                    encrypted_url,
                    encrypted_username,
                    encrypted_password,
                    username_selector,
                    password_selector,
                    submit_selector,
                ),
            )

            record_id = cursor.lastrowid

        if record_id is None:
            raise sqlite3.DatabaseError(
                "SQLite did not return a row id."
            )

        return int(record_id)

    def delete_record(
        self,
        record_id: int,
    ) -> bool:

        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM siteRecords
                WHERE rowid = ?
                """,
                (record_id,),
            )

        return cursor.rowcount > 0

    @staticmethod
    def _to_record(
        row: sqlite3.Row,
    ) -> SiteRecord:

        return SiteRecord(
            id=int(row["id"]),
            label=str(
                row["label"] or ""
            ),
            url=str(
                row["url"]
            ),
            username=str(
                row["username"]
            ),
            password=str(
                row["passwd"]
            ),
            username_selector=str(
                row["username_selector"] or ""
            ),
            password_selector=str(
                row["password_selector"] or ""
            ),
            submit_selector=str(
                row["submit_selector"] or ""
            ),
        )
