import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    r = client.get("/")
    assert r.status_code == 200
    assert "Enterprise RAG Lite" in r.json()["message"]


def test_upload_rejects_non_pdf():
    r = client.post("/api/documents/upload",
                    files={"file": ("test.txt", io.BytesIO(b"ciao"), "text/plain")})
    assert r.status_code == 400


def test_upload_rejects_rag_report_by_filename():
    """Guard anti GIGO: i report generati dal sistema vengono bloccati."""
    r = client.post("/api/documents/upload",
                    files={"file": ("report_2024.pdf", io.BytesIO(b"fake"), "application/pdf")})
    assert r.status_code == 400
    assert "report" in r.json()["detail"].lower()
