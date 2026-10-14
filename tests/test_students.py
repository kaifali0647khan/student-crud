import os

import pytest
from fastapi.testclient import TestClient

VALID = {
    "name": "Test Student",
    "date_of_birth": "2004-05-10",
    "email": "test@example.com",
    "phone": "+919812345678",
    "course": "Python",
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("STUDENTS_DB", str(tmp_path / "test.db"))
    from app.main import app

    with TestClient(app) as c:  # runs lifespan -> creates table
        yield c


def make(client, **over):
    return client.post("/students", json={**VALID, **over})


# ---------- Create ----------
def test_create_ok(client):
    r = make(client)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1 and body["name"] == "Test Student"


def test_create_requires_contact(client):
    r = make(client, email=None, phone=None)
    assert r.status_code == 422


def test_create_invalid_email(client):
    assert make(client, email="not-an-email").status_code == 422


def test_create_invalid_phone(client):
    assert make(client, phone="abc").status_code == 422


def test_create_future_dob(client):
    assert make(client, date_of_birth="2999-01-01").status_code == 422


def test_create_missing_name(client):
    bad = {k: v for k, v in VALID.items() if k != "name"}
    assert client.post("/students", json=bad).status_code == 422


def test_duplicate_email_409(client):
    assert make(client).status_code == 201
    assert make(client).status_code == 409


# ---------- Read ----------
def test_get_one_and_404(client):
    make(client)
    assert client.get("/students/1").json()["email"] == "test@example.com"
    assert client.get("/students/999").status_code == 404


def test_list_and_filters(client):
    make(client, name="Alice A", email="a@example.com", course="Python", date_of_birth="2004-01-01")
    make(client, name="Bob B", email="b@example.com", course="Data Science", date_of_birth="2006-06-06")
    r = client.get("/students")
    assert len(r.json()) == 2 and r.headers["X-Total-Count"] == "2"
    assert [s["name"] for s in client.get("/students?course=data").json()] == ["Bob B"]
    assert [s["name"] for s in client.get("/students?name=ali").json()] == ["Alice A"]
    assert [s["name"] for s in client.get("/students?born_after=2005-01-01").json()] == ["Bob B"]
    assert client.get("/students?born_after=bad-date").status_code == 422


def test_pagination(client):
    for i in range(5):
        make(client, name=f"Student {i}", email=f"s{i}@example.com")
    r = client.get("/students?limit=2&skip=1")
    assert [s["id"] for s in r.json()] == [2, 3]
    assert r.headers["X-Total-Count"] == "5"


# ---------- Update ----------
def test_patch_partial(client):
    make(client)
    r = client.patch("/students/1", json={"course": "Data Science"})
    assert r.status_code == 200
    assert r.json()["course"] == "Data Science" and r.json()["name"] == "Test Student"


def test_patch_empty_body_and_404(client):
    make(client)
    assert client.patch("/students/1", json={}).status_code == 422
    assert client.patch("/students/999", json={"course": "X"}).status_code == 404


def test_patch_cannot_remove_all_contact(client):
    make(client)
    r = client.patch("/students/1", json={"email": None, "phone": None})
    assert r.status_code == 422


def test_patch_duplicate_email(client):
    make(client, email="a@example.com")
    make(client, email="b@example.com")
    assert client.patch("/students/2", json={"email": "a@example.com"}).status_code == 409


def test_put_full_replace(client):
    make(client)
    new = {"name": "New Name", "date_of_birth": "2003-03-03", "phone": "+911234567890"}
    r = client.put("/students/1", json=new)
    assert r.status_code == 200
    assert r.json()["name"] == "New Name" and r.json()["email"] is None


# ---------- Delete ----------
def test_delete(client):
    make(client)
    assert client.delete("/students/1").status_code == 204
    assert client.get("/students/1").status_code == 404
    assert client.delete("/students/1").status_code == 404


# ---------- Persistence ----------
def test_data_persists_in_sqlite_file(client, tmp_path):
    make(client)
    import sqlite3

    rows = sqlite3.connect(str(tmp_path / "test.db")).execute("SELECT name FROM students").fetchall()
    assert rows == [("Test Student",)]
