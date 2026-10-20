"""
Tests for email verification and refresh-token revocation.
"""

from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.models.verification_token import VerificationToken


def _register(client, email="new@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "secret123", "full_name": "New User"},
    )
    assert response.status_code == 201, response.text
    return response


def _login(client, email="new@example.com", password="secret123"):
    return client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )


def test_register_without_verification_starts_a_session(client, user_payload):
    response = _register(client, user_payload["email"])
    assert response.json()["is_verified"] is True
    assert "access_token" in response.cookies


def test_register_with_verification_defers_the_session(client, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", True)
    response = _register(client)
    body = response.json()
    assert body["is_verified"] is False
    assert "access_token" not in response.cookies

    login = _login(client)
    assert login.status_code == 403
    assert login.json()["detail"] == "Email address is not verified"


def test_verify_email_token_unblocks_login(client, db, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", True)
    _register(client)

    stored = db.query(VerificationToken).one()
    assert stored.purpose == "email"
    assert stored.expires_at.replace(tzinfo=UTC) > datetime.now(UTC)

    response = client.get(f"/api/v1/auth/verify-email?token={stored.token}")
    assert response.status_code == 200, response.text
    assert response.json()["email"] == "new@example.com"

    assert _login(client).status_code == 200


def test_verify_email_rejects_unknown_token(client, db, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", True)
    _register(client)

    response = client.get("/api/v1/auth/verify-email?token=not-a-real-token")
    assert response.status_code == 400
    assert _login(client).status_code == 403


def test_verify_email_token_is_idempotent(client, db, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", True)
    _register(client)
    stored = db.query(VerificationToken).one()

    first = client.get(f"/api/v1/auth/verify-email?token={stored.token}")
    second = client.get(f"/api/v1/auth/verify-email?token={stored.token}")
    assert first.status_code == 200
    assert second.status_code == 200


def test_resend_verification_replaces_the_old_token(client, db, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", True)
    _register(client)
    old_token = db.query(VerificationToken).one().token

    resend = client.post("/api/v1/auth/resend-verification", json={"email": "new@example.com"})
    assert resend.status_code == 200, resend.text

    tokens = db.query(VerificationToken).all()
    assert len(tokens) == 1
    assert tokens[0].token != old_token
    assert client.get(f"/api/v1/auth/verify-email?token={old_token}").status_code == 400
    assert client.get(f"/api/v1/auth/verify-email?token={tokens[0].token}").status_code == 200


def test_resend_verification_does_not_leak_registrations(client, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", True)
    known = client.post("/api/v1/auth/resend-verification", json={"email": "new@example.com"})
    unknown = client.post("/api/v1/auth/resend-verification", json={"email": "nobody@example.com"})
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()


def test_resend_verification_skips_verified_accounts(client, db, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", True)
    _register(client)
    stored = db.query(VerificationToken).one()
    client.get(f"/api/v1/auth/verify-email?token={stored.token}")

    client.post("/api/v1/auth/resend-verification", json={"email": "new@example.com"})
    assert db.query(VerificationToken).count() == 1  # unchanged


def test_logout_revokes_the_refresh_token(client):
    login = _login_after_register(client)
    refresh_token = login.json()["refresh_token"]

    assert client.post("/api/v1/auth/logout").status_code == 200

    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh.status_code == 401
    assert refresh.json()["detail"] == "Refresh token revoked"


def test_logout_leaves_other_sessions_alone(client):
    login = _login_after_register(client)
    refresh_token = login.json()["refresh_token"]

    # A second device logs in and out; the first device's token still works.
    other = client.post(
        "/api/v1/auth/login",
        data={"username": "new@example.com", "password": "secret123"},
    )
    other_refresh = other.json()["refresh_token"]
    client.post("/api/v1/auth/logout", json={"refresh_token": other_refresh})

    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh.status_code == 200, refresh.text


def test_revoked_token_survives_cookie_roundtrip(client):
    """The refresh cookie is revoked too, not just an explicit body token."""
    _login_after_register(client)
    refresh_cookie = client.cookies.get("refresh_token")
    assert refresh_cookie

    client.post("/api/v1/auth/logout")
    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_cookie})
    assert refresh.status_code == 401


def _login_after_register(client):
    response = _register(client)
    assert response.status_code == 201, response.text
    login = _login(client)
    assert login.status_code == 200, login.text
    return login


def test_expired_verification_token_is_rejected(client, db, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", True)
    _register(client)
    stored = db.query(VerificationToken).one()
    stored.expires_at = datetime.now(UTC) - timedelta(hours=1)
    db.commit()

    response = client.get(f"/api/v1/auth/verify-email?token={stored.token}")
    assert response.status_code == 400
    assert _login(client).status_code == 403
