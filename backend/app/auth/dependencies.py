from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, sessionmaker

from backend.app.auth.security import AuthTokenError
from backend.app.auth.service import AuthService, AuthenticatedPrincipal
from backend.app.core.config import get_settings
from backend.app.db import create_session_factory


bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_auth_session_factory() -> sessionmaker[Session]:
    settings = get_settings()
    return create_session_factory(settings.database_url)


def get_auth_service() -> AuthService:
    settings = get_settings()
    return AuthService(
        session_factory=get_auth_session_factory(),
        jwt_secret=settings.secret_key,
        access_token_expire_minutes=settings.access_token_expire_minutes,
    )


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthenticatedPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return auth_service.authenticate_access_token(credentials.credentials)
    except AuthTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_roles(*allowed_roles: str):
    allowed_set = frozenset(allowed_roles)

    def dependency(
        principal: AuthenticatedPrincipal = Depends(get_current_principal),
    ) -> AuthenticatedPrincipal:
        if principal.role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
        return principal

    return dependency
