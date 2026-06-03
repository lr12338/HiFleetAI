from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets

import jwt


PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_DIGEST = "sha256"
PASSWORD_HASH_ITERATIONS = 390000
PASSWORD_SALT_BYTES = 16
JWT_ALGORITHM = "HS256"


class AuthTokenError(ValueError):
    """Raised when an access token cannot be validated."""


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    derived_key = hashlib.pbkdf2_hmac(
        PASSWORD_HASH_DIGEST,
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return (
        f"{PASSWORD_HASH_ALGORITHM}$"
        f"{PASSWORD_HASH_ITERATIONS}$"
        f"{salt.hex()}$"
        f"{derived_key.hex()}"
    )


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False

    try:
        algorithm, iteration_text, salt_hex, expected_hash_hex = stored_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != PASSWORD_HASH_ALGORITHM:
        return False

    try:
        iterations = int(iteration_text)
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(expected_hash_hex)
    except ValueError:
        return False

    actual_hash = hashlib.pbkdf2_hmac(
        PASSWORD_HASH_DIGEST,
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual_hash, expected_hash)


def create_access_token(
    *,
    subject: str,
    username: str,
    display_name: str,
    role: str,
    status: str,
    secret: str,
    expires_minutes: int,
    issued_at: datetime | None = None,
) -> str:
    now = issued_at or datetime.now(UTC)
    payload = {
        "sub": subject,
        "username": username,
        "display_name": display_name,
        "role": role,
        "status": status,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, *, secret: str) -> dict[str, object]:
    try:
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError as exc:
        raise AuthTokenError("Invalid access token") from exc

    if not isinstance(payload, dict):
        raise AuthTokenError("Invalid access token")
    return payload
