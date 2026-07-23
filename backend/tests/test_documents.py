def test_upload_rejects_unsupported_extension(client, auth_headers):
    files = {"file": ("malware.exe", b"fake binary content", "application/octet-stream")}
    r = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
    assert r.status_code == 400


def test_upload_and_list_txt_document(client, auth_headers):
    files = {"file": ("notes.txt", b"DOCBOT test content for indexing.", "text/plain")}
    r = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
    assert r.status_code == 201
    doc = r.json()
    assert doc["original_filename"] == "notes.txt"
    assert doc["status"] in ("pending", "processing", "indexed")

    r2 = client.get("/api/v1/documents", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["total"] == 1


def test_document_pipeline_indexes_txt_synchronously_in_test(client, auth_headers):
    # BackgroundTasks run after the response in production, but TestClient
    # executes them before returning control, so by the time we list, status
    # should have progressed to "indexed" for a trivial txt file.
    files = {"file": ("notes.txt", b"DOCBOT test content for indexing.", "text/plain")}
    client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
    r = client.get("/api/v1/documents", headers=auth_headers)
    doc = r.json()["documents"][0]
    assert doc["status"] == "indexed"
    assert doc["chunk_count"] >= 1


def test_documents_require_auth(client):
    r = client.get("/api/v1/documents")
    assert r.status_code == 401


def test_get_nonexistent_document_404s(client, auth_headers):
    r = client.get("/api/v1/documents/does-not-exist", headers=auth_headers)
    assert r.status_code == 404


def test_delete_document(client, auth_headers):
    files = {"file": ("notes.txt", b"Some content to delete.", "text/plain")}
    r = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
    doc_id = r.json()["id"]

    r2 = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert r2.status_code == 204

    r3 = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert r3.status_code == 404


def test_users_cannot_see_each_others_documents(client):
    # user A
    client.post(
        "/api/v1/auth/register",
        json={"email": "a@example.com", "full_name": "A", "password": "password123"},
    )
    a_token = client.post(
        "/api/v1/auth/login", json={"email": "a@example.com", "password": "password123"}
    ).json()["access_token"]

    client.post(
        "/api/v1/auth/register",
        json={"email": "b@example.com", "full_name": "B", "password": "password123"},
    )
    b_token = client.post(
        "/api/v1/auth/login", json={"email": "b@example.com", "password": "password123"}
    ).json()["access_token"]

    files = {"file": ("a_doc.txt", b"A's private content.", "text/plain")}
    client.post(
        "/api/v1/documents/upload", files=files, headers={"Authorization": f"Bearer {a_token}"}
    )

    r = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {b_token}"})
    assert r.json()["total"] == 0
