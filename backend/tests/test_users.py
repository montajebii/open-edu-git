"""
Tests for user endpoints.
"""


def test_get_user_by_id(client, auth):
    _, user = auth
    response = client.get(f"/api/v1/users/{user['id']}")
    assert response.status_code == 200
    assert response.json()["email"] == user["email"]


def test_get_missing_user_is_404(client):
    assert client.get("/api/v1/users/9999").status_code == 404


def test_update_own_profile(client, auth):
    headers, user = auth
    response = client.put(
        f"/api/v1/users/{user['id']}",
        headers=headers,
        json={"full_name": "Updated Name", "bio": "Maths teacher"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["full_name"] == "Updated Name"
    assert response.json()["bio"] == "Maths teacher"


def test_cannot_update_someone_else(client, auth):
    headers, _ = auth
    other = client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "password": "secret123", "full_name": "Other"},
    ).json()

    response = client.put(
        f"/api/v1/users/{other['id']}", headers=headers, json={"full_name": "Hacked"}
    )
    assert response.status_code == 403


def test_update_requires_authentication(anonymous, auth):
    _, user = auth
    anonymous.cookies.clear()
    assert anonymous.put(f"/api/v1/users/{user['id']}", json={"full_name": "x"}).status_code == 401
