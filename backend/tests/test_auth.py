"""
Tests for authentication endpoints.
"""


def test_register_creates_user_and_session(client, user_payload):
    response = client.post("/api/v1/auth/register", json=user_payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == user_payload["email"]
    assert "password" not in body
    assert "password_hash" not in body
    assert "access_token" in response.cookies


def test_register_rejects_duplicate_email(client, user_payload):
    assert client.post("/api/v1/auth/register", json=user_payload).status_code == 201
    duplicate = client.post("/api/v1/auth/register", json=user_payload)
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "Email already registered"


def test_login_returns_token_pair(client, user_payload):
    client.post("/api/v1/auth/register", json=user_payload)
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user_payload["email"], "password": user_payload["password"]},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_login_with_wrong_password_is_401(client, user_payload):
    client.post("/api/v1/auth/register", json=user_payload)
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user_payload["email"], "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_me_requires_a_token(anonymous, user_payload):
    anonymous.post("/api/v1/auth/register", json=user_payload)
    anonymous.cookies.clear()
    assert anonymous.get("/api/v1/auth/me").status_code in (401, 403)


def test_me_works_with_bearer_token(client, auth):
    headers, user = auth
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["email"] == user["email"]


def test_refresh_token_cannot_be_used_as_access_token(client, auth):
    headers, _ = auth
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "teacher@example.com", "password": "secret123"},
    )
    refresh_token = login.json()["refresh_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 401


def test_refresh_issues_a_new_token_pair(client, auth):
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "teacher@example.com", "password": "secret123"},
    )
    refresh_token = login.json()["refresh_token"]

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200, response.text
    assert response.json()["access_token"]


def test_refresh_rejects_garbage(client):
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": "nope"}).status_code == 401


def test_logout_clears_cookies(client, auth):
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.cookies.get("access_token") in (None, "")
