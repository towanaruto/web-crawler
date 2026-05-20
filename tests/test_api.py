import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.db.engine import get_db
from src.db.models import Base, CrawlJob, CrawlTarget


@pytest.fixture
def api_db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _override_db(session):
    def _get_db():
        yield session

    return _get_db


def test_health():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_target_crawl_returns_404_for_missing_target(api_db_session):
    app.dependency_overrides[get_db] = _override_db(api_db_session)
    client = TestClient(app)

    try:
        response = client.post(f"/crawl/{uuid.uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Crawl target not found"}


def test_list_crawl_jobs(api_db_session):
    target = CrawlTarget(base_url="https://example.com", crawl_mode="static")
    api_db_session.add(target)
    api_db_session.flush()
    job = CrawlJob(target_id=target.id, target_url="https://example.com/page")
    api_db_session.add(job)
    api_db_session.flush()

    app.dependency_overrides[get_db] = _override_db(api_db_session)
    client = TestClient(app)

    try:
        response = client.get("/crawl-jobs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(job.id)
    assert response.json()[0]["target_url"] == "https://example.com/page"
    assert response.json()[0]["status"] == "pending"
