from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db.config import get_runtime_database_url


def create_engine_for_url(database_url: str | None = None, *, echo: bool = False) -> Engine:
    resolved_url = database_url or get_runtime_database_url()
    connect_args = {"check_same_thread": False} if resolved_url.startswith("sqlite") else {}
    return create_engine(resolved_url, echo=echo, future=True, connect_args=connect_args)


def create_session_factory(database_url: str | None = None, *, echo: bool = False) -> sessionmaker[Session]:
    engine = create_engine_for_url(database_url, echo=echo)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
