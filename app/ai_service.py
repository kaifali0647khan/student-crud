"""
Optional bonus: ask natural-language questions about the students (local Ollama).

Safety design (as required by the assignment):
  * The model NEVER writes or runs SQL.
  * Our own backend code decides what to fetch (parameterised queries in crud.py).
  * Only those fetched records + a few computed facts are given to the model as context.
  * The model is told to answer only from that context.
"""
import os
import re
from typing import Optional

import httpx

from . import crud

OLLAMA_URL = lambda: os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = lambda: os.getenv("OLLAMA_MODEL", "llama3.2:1b")
MAX_RECORDS = 50  # keeps the prompt small for tiny models

SYSTEM_PROMPT = (
    "You are an assistant for a student database. Answer ONLY using the FACTS and "
    "RECORDS provided. Do not invent students or numbers. If the answer is not in the "
    "provided data, say you don't have that information. Keep the answer short and clear."
)


def retrieve(conn, question: str):
    """Decide which records to fetch based on simple, safe rules. Returns (facts, rows)."""
    q = question.lower()
    filters: dict = {}
    facts: list[str] = []

    total, _ = crud.list_students(conn, limit=1)
    facts.append(f"Total students in database: {total}")

    # "born after 2005" / "born before 2000" / "born in 2004"
    m = re.search(r"born\s+(after|before|in)\s+(\d{4})", q)
    if m:
        kind, year = m.group(1), int(m.group(2))
        from datetime import date

        if kind == "after":
            filters["born_after"] = date(year, 12, 31)
            facts.append(f"Filter applied: born after year {year} (i.e. born in {year + 1} or later)")
        elif kind == "before":
            filters["born_before"] = date(year, 1, 1)
            facts.append(f"Filter applied: born before year {year}")
        else:
            filters["born_after"] = date(year - 1, 12, 31)
            filters["born_before"] = date(year + 1, 1, 1)
            facts.append(f"Filter applied: born in {year}")

    # course mentioned in the question (matched against courses that really exist)
    for course in crud.distinct_courses(conn):
        if course.lower() in q:
            filters["course"] = course
            facts.append(f"Filter applied: course = {course}")
            break

    # "named Aarav" / "student Aarav"
    m = re.search(r"(?:named|called|student)\s+([a-z]+)", q)
    if m and "course" not in filters:
        filters["name"] = m.group(1)
        facts.append(f"Filter applied: name contains '{m.group(1)}'")

    matched, rows = crud.list_students(conn, limit=MAX_RECORDS, **filters)
    facts.append(f"Students matching the question's filters: {matched}")
    if matched > MAX_RECORDS:
        facts.append(f"Only the first {MAX_RECORDS} matching records are shown below")
    return facts, rows


def build_prompt(question: str, facts: list[str], rows) -> str:
    lines = [
        f"- id={r['id']}, name={r['name']}, dob={r['date_of_birth']}, course={r['course']}, "
        f"email={r['email']}, phone={r['phone']}"
        for r in rows
    ]
    records = "\n".join(lines) if lines else "(no matching records)"
    return f"FACTS:\n" + "\n".join(f"- {f}" for f in facts) + f"\n\nRECORDS:\n{records}\n\nQUESTION: {question}"


def ask_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL(),
        "stream": False,
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    r = httpx.post(f"{OLLAMA_URL()}/api/chat", json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()
