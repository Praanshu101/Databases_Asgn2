from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "app.db"
INIT_SQL = BASE_DIR / "sql" / "init.sql"
INDEX_SQL = BASE_DIR / "sql" / "indexes.sql"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    with conn:
        conn.executescript(INIT_SQL.read_text(encoding="utf-8"))
    conn.close()


def apply_indexes() -> None:
    conn = get_connection()
    with conn:
        conn.executescript(INDEX_SQL.read_text(encoding="utf-8"))
    conn.close()
