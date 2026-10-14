"""SQLite connection + table creation (plain sqlite3, no ORM)."""
import os
import sqlite3


def db_path() -> str:
    # Read at call time so tests can point to a temporary database.
    return os.getenv("STUDENTS_DB", "students.db")


def get_conn():
    """FastAPI dependency: one connection per request, always closed."""
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    conn = sqlite3.connect(db_path())
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            date_of_birth   TEXT NOT NULL,          -- ISO format YYYY-MM-DD
            email           TEXT UNIQUE,
            phone           TEXT,
            course          TEXT,
            address         TEXT,
            enrollment_date TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    conn.close()
