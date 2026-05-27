import pytest
from sqlalchemy import create_engine, event, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB

from src.db.models import Base
from src.db.models import User


@event.listens_for(Base.metadata, "before_create")
def _remap_jsonb_for_sqlite(target, connection, **kw):
    """Replace JSONB with JSON for SQLite compatibility in tests."""
    if connection.dialect.name == "sqlite":
        for table in target.tables.values():
            for col in table.columns:
                if isinstance(col.type, JSONB):
                    col.type = JSON()


@event.listens_for(Base.metadata, "before_create")
def _strip_pg_only_defaults_for_sqlite(target, connection, **kw):
    """SQLite has no gen_random_uuid(); SQLAlchemy still emits the server
    default in CREATE TABLE. Drop the server_default for tests so DDL parses,
    and rely on the Python-side default=uuid.uuid4 instead."""
    if connection.dialect.name == "sqlite":
        for table in target.tables.values():
            for col in table.columns:
                if col.server_default is not None:
                    sd_text = getattr(col.server_default, "arg", None)
                    if sd_text is not None and "gen_random_uuid" in str(sd_text):
                        col.server_default = None


@pytest.fixture
def db_session():
    """Create an in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def auth_user(db_session):
    user = User(auth0_sub="auth0|test-user", email="user@example.com")
    db_session.add(user)
    db_session.flush()
    return user
