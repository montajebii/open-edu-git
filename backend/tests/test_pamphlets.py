"""
Tests for the pamphlet vertical slice: create -> list -> search -> version -> fork.
"""

import pytest

from app.api.v1.endpoints import pamphlet as pamphlet_module

NEW_PAMPHLET = {
    "title": "مشتق و کاربردهایش",
    "grade": "دوازدهم",
    "subject": "ریاضی",
    "chapter": "مشتق",
    "method": "حل مسئله",
    "difficulty": "متوسط",
    "is_public": 1,
    "tags": ["کنکوری", "مثال‌محور"],
}


@pytest.fixture
def fake_storage(monkeypatch):
    """Replace MinIO with an in-memory no-op."""

    class FakeMinio:
        def put_object(self, *args, **kwargs):
            return None

    monkeypatch.setattr(pamphlet_module, "minio_client", FakeMinio())
    return FakeMinio()


def test_create_pamphlet(client, auth):
    headers, user = auth
    response = client.post("/api/v1/pamphlets/", headers=headers, json=NEW_PAMPHLET)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["author_id"] == user["id"]
    # Regression: updated_at used to be NULL, which broke the response model.
    assert body["created_at"]
    assert body["updated_at"]


def test_create_pamphlet_requires_authentication(client):
    assert client.post("/api/v1/pamphlets/", json=NEW_PAMPHLET).status_code == 401


def test_list_and_search(client, auth):
    headers, _ = auth
    client.post("/api/v1/pamphlets/", headers=headers, json=NEW_PAMPHLET)
    client.post(
        "/api/v1/pamphlets/",
        headers=headers,
        json={**NEW_PAMPHLET, "title": "الکتریسیته", "subject": "فیزیک", "chapter": "جریان"},
    )

    everything = client.get("/api/v1/pamphlets/")
    assert everything.status_code == 200, everything.text
    assert len(everything.json()) == 2

    found = client.get("/api/v1/pamphlets/", params={"search": "الکتریسیته"})
    assert found.status_code == 200, found.text
    assert [p["title"] for p in found.json()] == ["الکتریسیته"]

    filtered = client.get("/api/v1/pamphlets/", params={"subject": "ریاضی"})
    assert [p["title"] for p in filtered.json()] == [NEW_PAMPHLET["title"]]


def test_search_treats_wildcards_literally(client, auth):
    headers, _ = auth
    client.post("/api/v1/pamphlets/", headers=headers, json=NEW_PAMPHLET)

    response = client.get("/api/v1/pamphlets/", params={"search": "%"})
    assert response.status_code == 200
    assert response.json() == []


def test_private_pamphlet_is_hidden_from_others(client, auth):
    headers, _ = auth
    created = client.post(
        "/api/v1/pamphlets/", headers=headers, json={**NEW_PAMPHLET, "is_public": 0}
    ).json()
    pamphlet_id = created["id"]

    client.cookies.clear()  # act as a logged-out visitor
    assert client.get("/api/v1/pamphlets/").json() == []
    assert client.get(f"/api/v1/pamphlets/{pamphlet_id}").status_code == 404

    # The owner still sees it in the list and can open it.
    owned = client.get("/api/v1/pamphlets/", headers=headers)
    assert [p["id"] for p in owned.json()] == [pamphlet_id]
    assert client.get(f"/api/v1/pamphlets/{pamphlet_id}", headers=headers).status_code == 200


def test_upload_version(client, auth, fake_storage):
    headers, _ = auth
    pamphlet = client.post("/api/v1/pamphlets/", headers=headers, json=NEW_PAMPHLET).json()

    response = client.post(
        f"/api/v1/pamphlets/{pamphlet['id']}/versions",
        headers=headers,
        files={"file": ("notes.pdf", b"%PDF-1.4 test", "application/pdf")},
        data={"version_number": "1", "notes": "نسخه اول"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["version_number"] == 1
    assert body["file_type"] == "pdf"
    assert body["file_size"] == len(b"%PDF-1.4 test")


def test_version_number_auto_increments(client, auth, fake_storage):
    headers, _ = auth
    pamphlet = client.post("/api/v1/pamphlets/", headers=headers, json=NEW_PAMPHLET).json()
    url = f"/api/v1/pamphlets/{pamphlet['id']}/versions"

    first = client.post(url, headers=headers, files={"file": ("a.md", b"# one", "text/markdown")})
    second = client.post(url, headers=headers, files={"file": ("b.md", b"# two", "text/markdown")})
    assert first.json()["version_number"] == 1
    assert second.json()["version_number"] == 2


def test_only_author_can_upload_version(client, auth, fake_storage):
    headers, _ = auth
    pamphlet = client.post("/api/v1/pamphlets/", headers=headers, json=NEW_PAMPHLET).json()

    client.post(
        "/api/v1/auth/register",
        json={"email": "o@x.com", "password": "secret123", "full_name": "O"},
    )
    login = client.post("/api/v1/auth/login", data={"username": "o@x.com", "password": "secret123"})
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.post(
        f"/api/v1/pamphlets/{pamphlet['id']}/versions",
        headers=other_headers,
        files={"file": ("x.pdf", b"data", "application/pdf")},
    )
    assert response.status_code == 403


def test_reviews(client, auth):
    headers, _ = auth
    pamphlet = client.post("/api/v1/pamphlets/", headers=headers, json=NEW_PAMPHLET).json()
    url = f"/api/v1/reviews/pamphlets/{pamphlet['id']}/reviews"

    created = client.post(url, headers=headers, json={"rating": 5, "comment": "عالی"})
    assert created.status_code == 200, created.text
    assert created.json()["updated_at"]

    duplicate = client.post(url, headers=headers, json={"rating": 4})
    assert duplicate.status_code == 400

    listed = client.get(url)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_fork_creates_a_copy(client, auth, fake_storage):
    headers, _ = auth
    pamphlet = client.post("/api/v1/pamphlets/", headers=headers, json=NEW_PAMPHLET).json()
    client.post(
        f"/api/v1/pamphlets/{pamphlet['id']}/versions",
        headers=headers,
        files={"file": ("n.pdf", b"data", "application/pdf")},
    )

    response = client.post(f"/api/v1/pamphlets/{pamphlet['id']}/fork", headers=headers)
    assert response.status_code == 201, response.text
    fork = response.json()
    assert fork["original_pamphlet_id"] == pamphlet["id"]
    assert fork["new_pamphlet_id"] != pamphlet["id"]

    copy = client.get(f"/api/v1/pamphlets/{fork['new_pamphlet_id']}", headers=headers).json()
    assert copy["title"].endswith("(fork)")


def test_cannot_fork_pamphlet_without_versions(client, auth):
    headers, _ = auth
    pamphlet = client.post("/api/v1/pamphlets/", headers=headers, json=NEW_PAMPHLET).json()
    response = client.post(f"/api/v1/pamphlets/{pamphlet['id']}/fork", headers=headers)
    assert response.status_code == 400
