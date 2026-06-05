from __future__ import annotations

import argparse
import secrets
import string
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select

from backend.app.auth.service import AuthService
from backend.app.core.config import get_settings
from backend.app.db import create_session_factory
from backend.app.models import User


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a local HiFleetAI admin user for console login.",
    )
    parser.add_argument("--env-file", default=None, help="Optional env file path.")
    parser.add_argument("--username", default="admin", help="Admin username.")
    parser.add_argument("--display-name", default="Local Admin", help="Admin display name.")
    parser.add_argument(
        "--password",
        default=None,
        help="Admin password. If omitted, a random password is generated and printed once.",
    )
    return parser


def generate_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings(env_file=args.env_file)
    session_factory = create_session_factory(settings.database_url)
    auth_service = AuthService(
        session_factory=session_factory,
        jwt_secret=settings.secret_key,
        access_token_expire_minutes=settings.access_token_expire_minutes,
    )

    with session_factory() as session:
        existing_user = session.scalar(select(User).where(User.username == args.username))

    if existing_user is not None:
        print("Local admin already exists.")
        print(f"username={existing_user.username}")
        print(f"display_name={existing_user.display_name}")
        print(f"role={existing_user.role}")
        print(f"status={existing_user.status}")
        return 0

    password = args.password or generate_password()
    created_user = auth_service.create_local_user(
        username=args.username,
        password=password,
        display_name=args.display_name,
        role="admin",
    )

    print("Local admin created successfully.")
    print(f"username={created_user.username}")
    print(f"display_name={created_user.display_name}")
    print(f"role={created_user.role}")
    print(f"password={password}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI fallback path
        print(f"bootstrap_local_admin failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
