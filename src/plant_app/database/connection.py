"""Database layer.

Two modes:
* ``sqlite`` (default) - zero-setup demonstration database created on demand;
  the basic app never requires a personal MySQL server.
* ``mysql`` - for real deployments; credentials come from environment
  variables and the schema is applied with ``scripts/schema_mysql.sql``.

All user-facing queries use parameter binding. No credentials are hardcoded.
"""
from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ..config import DEMO_DATA_DIR, get_settings

logger = logging.getLogger(__name__)


class DatabaseUnavailableError(RuntimeError):
    """Raised when the configured database cannot be reached."""


@contextmanager
def get_connection() -> Iterator[Any]:
    settings = get_settings()
    if settings.db_mode == "mysql":
        try:
            import mysql.connector
        except ImportError as exc:
            raise DatabaseUnavailableError(
                "DB_MODE=mysql but mysql-connector-python is not installed. "
                "Install it or set DB_MODE=sqlite."
            ) from exc
        try:
            conn = mysql.connector.connect(
                host=settings.db_host,
                port=settings.db_port,
                user=settings.db_user,
                password=settings.db_password,
                database=settings.db_name,
                connection_timeout=5,
            )
        except Exception as exc:
            raise DatabaseUnavailableError(
                f"MySQL connection failed: {exc}. Check DB_* variables in .env."
            ) from exc
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
        return

    DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_path = DEMO_DATA_DIR / "app_demo.db"
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_sqlite_schema(conn)
        yield conn
        conn.commit()
    finally:
        conn.close()


def _ensure_sqlite_schema(conn: sqlite3.Connection) -> None:
    schema = Path(__file__).resolve().parent.parent.parent / "scripts" / "schema_sqlite.sql"
    if schema.exists():
        conn.executescript(schema.read_text(encoding="utf-8"))
    else:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS crops ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, crop_name TEXT NOT NULL,"
            "field_name TEXT, quantity REAL, planting_date TEXT, harvest_date TEXT,"
            "notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )


# --- Crop records -------------------------------------------------------------

def insert_crop_record(crop_name: str, field_name: str, quantity: float,
                       planting_date: str, harvest_date: str, notes: str) -> int:
    if not crop_name or not crop_name.strip():
        raise ValueError("Crop name is required.")
    if quantity is not None:
        try:
            quantity = float(quantity)
        except (TypeError, ValueError) as exc:
            raise ValueError("Quantity must be a number.") from exc
        if quantity < 0 or quantity > 1_000_000:
            raise ValueError("Quantity must be between 0 and 1,000,000.")
    with get_connection() as conn:
        cur = conn.cursor()
        if get_settings().db_mode == "mysql":
            cur.callproc("InsertCrop", (crop_name.strip(), field_name, quantity, planting_date, harvest_date, notes))
        else:
            cur.execute(
                "INSERT INTO crops (crop_name, field_name, quantity, planting_date, harvest_date, notes)"
                " VALUES (?,?,?,?,?,?)",
                (crop_name.strip(), field_name, quantity, planting_date, harvest_date, notes),
            )
        return int(cur.lastrowid) if cur.lastrowid is not None else 0


def list_crop_records(limit: int = 200) -> list[dict]:
    if limit < 1 or limit > 1000:
        raise ValueError("limit must be between 1 and 1000.")
    with get_connection() as conn:
        cur = conn.cursor()
        if get_settings().db_mode == "mysql":
            cur.execute(
                "SELECT id, crop_name, field_name, quantity, planting_date, harvest_date, notes"
                " FROM Crops ORDER BY id DESC LIMIT %s", (limit,)
            )
        else:
            cur.execute(
                "SELECT id, crop_name, field_name, quantity, planting_date, harvest_date, notes"
                " FROM crops ORDER BY id DESC LIMIT ?", (limit,)
            )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
