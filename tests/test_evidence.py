from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_upload_success():
    payload = b"approval date: 2024-01-05\namount: 1,200.00\n"
    response = client.post(
        "/evidence/upload",
        files={"file": ("evidence.txt", payload, "text/plain")},
        data={"notes": "sample upload"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "evidence.txt"
    assert body["size_bytes"] == len(payload)
    assert body["sha256"]
    assert body["notes"] == "sample upload"


def test_upload_empty_file_returns_400():
    response = client.post(
        "/evidence/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_control_not_found_returns_404():
    response = client.post(
        "/evidence/upload",
        files={"file": ("evidence.txt", b"data", "text/plain")},
        data={"control_id": "missing-control"},
    )
    assert response.status_code == 404


def test_download_returns_bytes_and_headers():
    payload = b"download me"
    upload_response = client.post(
        "/evidence/upload",
        files={"file": ("download.bin", payload, "application/octet-stream")},
    )
    evidence = upload_response.json()
    download_response = client.get(f"/evidence/{evidence['id']}/download")
    assert download_response.status_code == 200
    assert download_response.content == payload
    assert "attachment" in download_response.headers.get("content-disposition", "")
