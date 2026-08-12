"""Per-branch SQLite engine/session setup and seeding."""

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.branch.models import Base, Account
from backend.shared.config import database_path, SEED_ACCOUNTS


def make_session_factory(branch_id: int, db_path: str | None = None):
    """Create the engine/tables for one branch and return a session factory."""
    path = db_path or database_path(branch_id)
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None

    engine = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    _seed_accounts(session_factory)
    return session_factory


def _seed_accounts(session_factory):
    session = session_factory()
    try:
        if session.query(Account).count() == 0:
            now = datetime.now(timezone.utc)
            for account_id, balance in SEED_ACCOUNTS.items():
                session.add(Account(account_id=account_id, balance=balance, updated_at=now))
            session.commit()
    finally:
        session.close()
