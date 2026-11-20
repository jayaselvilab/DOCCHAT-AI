import pytest
from fastapi.testclient import TestClient

from app import config, rag as rag_module
from app.main import app, rag


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """A client whose documents live in a temp folder, with no API key."""
    (tmp_path / "leave.txt").write_text(
        "Employees get 18 days of paid annual leave each year. "
        "Up to 10 unused days carry forward to next year."
    )
    monkeypatch.setattr(config, "DOCS_DIR", tmp_path)
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    rag.documents.clear()
    with TestClient(app) as test_client:  # runs lifespan, loads tmp_path
        yield test_client
    rag.documents.clear()


def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["documents"] == 1
    assert body["claude_enabled"] is False


def test_ask_retrieval_only_mode(client):
    body = client.post("/api/ask", json={"question": "how many days of annual leave?"}).json()
    assert body["mode"] == "retrieval_only"
    assert "18 days" in body["answer"]
    assert body["sources"][0]["label"] == "leave.txt #0"


def test_ask_no_match(client):
    body = client.post("/api/ask", json={"question": "quantum chromodynamics"}).json()
    assert body["mode"] == "no_match"
    assert body["sources"] == []


def test_ask_uses_claude_when_key_set(client, monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(rag_module, "ask_claude", lambda q, hits: "18 days [leave.txt #0]")
    body = client.post("/api/ask", json={"question": "annual leave days?"}).json()
    assert body["mode"] == "claude"
    assert body["answer"] == "18 days [leave.txt #0]"


def test_upload_then_ask(client):
    files = {"file": ("travel.txt", b"Hotel stays are capped at 5000 rupees per night.", "text/plain")}
    assert client.post("/api/upload", files=files).status_code == 200
    names = [d["name"] for d in client.get("/api/documents").json()["documents"]]
    assert "travel.txt" in names
    body = client.post("/api/ask", json={"question": "hotel cap per night"}).json()
    assert body["sources"][0]["label"].startswith("travel.txt")


def test_upload_rejects_wrong_type(client):
    files = {"file": ("evil.exe", b"MZ", "application/octet-stream")}
    assert client.post("/api/upload", files=files).status_code == 400


def test_upload_strips_path_from_filename(client, tmp_path):
    files = {"file": ("../../escape.txt", b"some harmless words here", "text/plain")}
    assert client.post("/api/upload", files=files).status_code == 200
    assert (tmp_path / "escape.txt").exists()


def test_delete_document(client):
    assert client.delete("/api/documents/leave.txt").status_code == 200
    assert client.delete("/api/documents/leave.txt").status_code == 404


def test_ask_validates_input(client):
    assert client.post("/api/ask", json={"question": "a"}).status_code == 422


def test_ask_without_documents(client):
    client.delete("/api/documents/leave.txt")
    assert client.post("/api/ask", json={"question": "anything at all"}).status_code == 400
