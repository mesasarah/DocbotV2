def test_health_check(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_creates_first_user_as_admin(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "full_name": "Admin", "password": "password123"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["role"] == "admin"
    assert "access_token" in body
    assert "refresh_token" in body


def test_second_user_registered_as_regular_user(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "first@example.com", "full_name": "First", "password": "password123"},
    )
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "second@example.com", "full_name": "Second", "password": "password123"},
    )
    assert r.json()["user"]["role"] == "user"


def test_duplicate_email_registration_rejected(client):
    payload = {"email": "dup@example.com", "full_name": "Dup", "password": "password123"}
    client.post("/api/v1/auth/register", json=payload)
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 409


def test_login_with_wrong_password_fails(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "full_name": "User", "password": "correctpassword"},
    )
    r = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "wrongpassword"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_me_with_valid_token(client, auth_headers):
    r = client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "test@example.com"


def test_refresh_token_flow(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@example.com", "full_name": "Refresh", "password": "password123"},
    )
    refresh_token = r.json()["refresh_token"]
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r2.status_code == 200
    assert "access_token" in r2.json()
