from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import Base, create_engine_for_url
from backend.app.main import create_app


def build_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine_for_url(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def build_client(tmp_path):
    from backend.app.auth.dependencies import get_auth_service
    from backend.app.auth.service import AuthService

    database_url = f"sqlite:///{tmp_path / 'auth-test.db'}"
    session_factory = build_session_factory(database_url)
    auth_service = AuthService(
        session_factory=session_factory,
        jwt_secret="unit-test-secret-key-with-32-bytes",
        access_token_expire_minutes=15,
    )
    auth_service.create_local_user(
        username="admin_user",
        password="correct-password",
        display_name="Admin User",
        role="admin",
    )

    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    client = TestClient(app)
    return client, auth_service


def test_login_succeeds_with_valid_credentials(tmp_path) -> None:
    client, _ = build_client(tmp_path)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin_user",
            "password": "correct-password",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["expires_in"] == 900
    assert payload["user"] == {
        "username": "admin_user",
        "display_name": "Admin User",
        "role": "admin",
        "status": "active",
    }


def test_login_rejects_invalid_password(tmp_path) -> None:
    client, _ = build_client(tmp_path)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin_user",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}


def test_protected_endpoint_requires_login(tmp_path) -> None:
    client, _ = build_client(tmp_path)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_me_returns_authenticated_user_profile(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin_user",
            "password": "correct-password",
        },
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "username": "admin_user",
        "display_name": "Admin User",
        "role": "admin",
        "status": "active",
    }


def test_access_token_round_trip_preserves_role(tmp_path) -> None:
    _, auth_service = build_client(tmp_path)
    login_result = auth_service.login(username="admin_user", password="correct-password")

    principal = auth_service.authenticate_access_token(login_result.access_token)

    assert principal.username == "admin_user"
    assert principal.display_name == "Admin User"
    assert principal.role == "admin"
    assert principal.status == "active"
