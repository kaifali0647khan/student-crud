"""Insert DUMMY students for demo/testing. Run: python seed.py"""
import sqlite3

from app import crud
from app.database import db_path, init_db

DUMMY = [
    ("Aarav Sharma", "2004-03-15", "aarav.sharma@example.com", "+919800000001", "Python Development", "2024-07-01"),
    ("Diya Verma", "2005-11-02", "diya.verma@example.com", "+919800000002", "Data Science", "2024-07-01"),
    ("Rohan Gupta", "2006-01-20", "rohan.gupta@example.com", None, "Python Development", "2025-01-10"),
    ("Ananya Singh", "2003-08-09", "ananya.singh@example.com", "+919800000004", "Web Development", "2023-07-15"),
    ("Kabir Khan", "2007-05-30", None, "+919800000005", "Data Science", "2025-07-01"),
    ("Meera Iyer", "2005-02-14", "meera.iyer@example.com", "+919800000006", "Web Development", "2024-01-05"),
    ("Vihaan Patel", "2006-09-25", "vihaan.patel@example.com", "+919800000007", "Python Development", "2025-01-10"),
    ("Ishita Joshi", "2002-12-01", "ishita.joshi@example.com", "+919800000008", "Data Science", "2022-07-01"),
]

if __name__ == "__main__":
    from datetime import date

    init_db()
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    if conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] > 0:
        print("Table already has data; skipping seed.")
        conn.close()
        raise SystemExit(0)
    added = 0
    for name, dob, email, phone, course, enr in DUMMY:
        try:
            crud.create_student(conn, dict(
                name=name, date_of_birth=date.fromisoformat(dob), email=email,
                phone=phone, course=course, enrollment_date=date.fromisoformat(enr)))
            added += 1
        except sqlite3.IntegrityError:
            pass  # already seeded (duplicate email)
    conn.close()
    print(f"Seeded {added} dummy students.")
