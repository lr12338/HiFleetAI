from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.auth.security import AuthTokenError, create_access_token, hash_password, verify_password
from backend.app.models import User


VALID_ROLES = frozenset({"admin", "agent", "viewer"})
USER_TYPE_BY_ROLE = {
    "admin": "admin",
    "agent": "internal_employee",
    "viewer": "internal_employee",
}


class InvalidCredentialsError(ValueError):
    """Raised when username or password validation fails."""


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    user_id: str
    username: str
    display_name: str
    role: str
    status: str


@dataclass(frozen=True)
class LoginResult:
    access_token: str
    token_type: str
    expires_in: int
    user: AuthenticatedPrincipal


class AuthService:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        jwt_secret: str,
        access_token_expire_minutes: int,
    ) -> None:
        self._session_factory = session_factory
        self._jwt_secret = jwt_secret
        self._access_token_expire_minutes = access_token_expire_minutes

    def create_local_user(
        self,
        *,
        username: str,
        password: str,
        display_name: str,
        role: str,
        status: str = "active",
    ) -> User:
        normalized_username = self._normalize_username(username)
        self._validate_role(role)

        with self._session_factory() as session:
            existing_user = self._get_user_by_username(session=session, username=normalized_username)
            if existing_user is not None:
                raise ValueError(f"User '{normalized_username}' already exists.")

            user = User(
                display_name=display_name,
                user_type=USER_TYPE_BY_ROLE[role],
                status=status,
                username=normalized_username,
                password_hash=hash_password(password),
                role=role,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def login(self, *, username: str, password: str) -> LoginResult:
        normalized_username = self._normalize_username(username)

        with self._session_factory() as session:
            user = self._get_user_by_username(session=session, username=normalized_username)
            if user is None or not self._can_authenticate(user=user):
                raise InvalidCredentialsError("Invalid username or password")

            if not verify_password(password, user.password_hash):
                raise InvalidCredentialsError("Invalid username or password")

            principal = self._build_principal(user)
            access_token = create_access_token(
                subject=principal.user_id,
                username=principal.username,
                display_name=principal.display_name,
                role=principal.role,
                status=principal.status,
                secret=self._jwt_secret,
                expires_minutes=self._access_token_expire_minutes,
            )
            return LoginResult(
                access_token=access_token,
                token_type="bearer",
                expires_in=self._access_token_expire_minutes * 60,
                user=principal,
            )

    def authenticate_access_token(self, token: str) -> AuthenticatedPrincipal:
        payload = self._decode_token(token)
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject:
            raise AuthTokenError("Invalid access token")

        with self._session_factory() as session:
            user = session.get(User, subject)
            if user is None or not self._can_authenticate(user=user):
                raise AuthTokenError("Invalid access token")
            return self._build_principal(user)

    def _decode_token(self, token: str) -> dict[str, object]:
        from backend.app.auth.security import decode_access_token

        return decode_access_token(token, secret=self._jwt_secret)

    @staticmethod
    def _normalize_username(username: str) -> str:
        normalized_username = username.strip()
        if not normalized_username:
            raise InvalidCredentialsError("Invalid username or password")
        return normalized_username

    @staticmethod
    def _validate_role(role: str) -> None:
        if role not in VALID_ROLES:
            raise ValueError(f"Unsupported role '{role}'.")

    @staticmethod
    def _build_principal(user: User) -> AuthenticatedPrincipal:
        if user.username is None or user.role is None:
            raise AuthTokenError("Invalid access token")
        return AuthenticatedPrincipal(
            user_id=user.id,
            username=user.username,
            display_name=user.display_name,
            role=user.role,
            status=user.status,
        )

    @staticmethod
    def _can_authenticate(*, user: User) -> bool:
        return (
            user.username is not None
            and user.password_hash is not None
            and user.role in VALID_ROLES
            and user.status == "active"
        )

    @staticmethod
    def _get_user_by_username(*, session: Session, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        return session.scalar(statement)
