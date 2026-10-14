"""All SQL lives here. Every query is parameterised (no SQL injection)."""
import sqlite3
from datetime import date
from typing import Optional

COLUMNS = ["name", "date_of_birth", "email", "phone", "course", "address", "enrollment_date"]


def _to_db(data: dict) -> dict:
    """Convert date objects to ISO strings for SQLite."""
    return {k: (v.isoformat() if isinstance(v, date) else v) for k, v in data.items()}


def create_student(conn: sqlite3.Connection, data: dict) -> int:
    data = _to_db(data)
    cols = [c for c in COLUMNS if c in data]
    sql = f"INSERT INTO students ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})"
    cur = conn.execute(sql, [data[c] for c in cols])
    conn.commit()
    return cur.lastrowid


def get_student(conn: sqlite3.Connection, student_id: int) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()


def list_students(
    conn: sqlite3.Connection,
    name: Optional[str] = None,
    course: Optional[str] = None,
    email: Optional[str] = None,
    born_after: Optional[date] = None,
    born_before: Optional[date] = None,
    skip: int = 0,
    limit: int = 50,
):
    where, params = [], []
    if name:
        where.append("name LIKE ?")
        params.append(f"%{name}%")
    if course:
        where.append("course LIKE ?")
        params.append(f"%{course}%")
    if email:
        where.append("email = ?")
        params.append(email.lower())
    if born_after:
        where.append("date_of_birth > ?")
        params.append(born_after.isoformat())
    if born_before:
        where.append("date_of_birth < ?")
        params.append(born_before.isoformat())
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    count = conn.execute(f"SELECT COUNT(*) FROM students {clause}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM students {clause} ORDER BY id LIMIT ? OFFSET ?",
        params + [limit, skip],
    ).fetchall()
    return count, rows


def update_student(conn: sqlite3.Connection, student_id: int, data: dict) -> None:
    data = _to_db(data)
    cols = [c for c in COLUMNS if c in data]
    if not cols:
        return
    sets = ", ".join(f"{c} = ?" for c in cols) + ", updated_at = datetime('now')"
    conn.execute(f"UPDATE students SET {sets} WHERE id = ?", [data[c] for c in cols] + [student_id])
    conn.commit()


def delete_student(conn: sqlite3.Connection, student_id: int) -> bool:
    cur = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    return cur.rowcount > 0


def distinct_courses(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT DISTINCT course FROM students WHERE course IS NOT NULL").fetchall()
    return [r[0] for r in rows]
