"""AI tests mock Ollama, so they run without it installed."""
import httpx
import pytest
from fastapi.testclient import TestClient

from app import ai_service


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("STUDENTS_DB", str(tmp_path / "ai.db"))
    from app.main import app

    with TestClient(app) as c:
        for n, dob, em, course in [
            ("Old One", "2000-01-01", "o@example.com", "Python"),
            ("Young One", "2006-05-05", "y@example.com", "Data Science"),
            ("Young Two", "2007-07-07", "z@example.com", "Python"),
        ]:
            c.post("/students", json={"name": n, "date_of_birth": dob, "email": em, "course": course})
        yield c


def test_context_is_grounded_in_db(client, monkeypatch):
    seen = {}

    def fake(prompt):
        seen["prompt"] = prompt
        return "mocked answer"

    monkeypatch.setattr(ai_service, "ask_ollama", fake)
    r = client.post("/ai/ask", json={"question": "List students born after 2005"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "mocked answer" and body["records_used"] == 2
    assert "Young One" in seen["prompt"] and "Young Two" in seen["prompt"]
    assert "Old One" not in seen["prompt"]  # filtered out by backend code, not by the model


def test_count_question_has_total_fact(client, monkeypatch):
    monkeypatch.setattr(ai_service, "ask_ollama", lambda p: "3")
    body = client.post("/ai/ask", json={"question": "How many students are there?"}).json()
    assert "Total students in database: 3" in body["facts"]


def test_course_filter(client, monkeypatch):
    monkeypatch.setattr(ai_service, "ask_ollama", lambda p: "ok")
    body = client.post("/ai/ask", json={"question": "Who is in Data Science?"}).json()
    assert body["records_used"] == 1


def test_ollama_down_returns_503(client, monkeypatch):
    def boom(prompt):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(ai_service, "ask_ollama", boom)
    r = client.post("/ai/ask", json={"question": "How many students are there?"})
    assert r.status_code == 503 and "Ollama is not running" in r.json()["detail"]


def test_question_too_short(client):
    assert client.post("/ai/ask", json={"question": "hi"}).status_code == 422
