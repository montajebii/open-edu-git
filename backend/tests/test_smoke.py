"""
Smoke tests: the application must start and expose the documented routers.
"""


def test_root_and_health(client):
    assert client.get("/").status_code == 200
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}


def test_openapi_docs_available(client):
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json")
    assert schema.status_code == 200
    assert "/api/v1/auth/login" in schema.json()["paths"]


def test_all_routers_are_mounted(client):
    paths = {
        route.path for route in client.app.routes if getattr(route, "path", "").startswith("/api")
    }
    expected = {
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/me",
        "/api/v1/users/{user_id}",
        "/api/v1/pamphlets/",
        "/api/v1/pamphlets/{pamphlet_id}/versions",
        "/api/v1/reviews/pamphlets/{pamphlet_id}/reviews",
        "/api/v1/pamphlets/{pamphlet_id}/fork",
        "/api/v1/storage/upload/{bucket_name}",
    }
    missing = expected - paths
    assert not missing, f"routers not mounted: {sorted(missing)}"
