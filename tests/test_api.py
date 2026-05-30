import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api import app as api_app
from src.auth.invites import create_invite
from src.config.settings import settings
from src.db.engine import get_db
from src.db.models import Base, CrawlJob, CrawlTarget, User

app = api_app.app


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


def _user(session, email="user@example.com"):
    user = User(auth0_sub=f"auth0|{email}", email=email)
    session.add(user)
    session.flush()
    return user


def test_health():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_target_crawl_returns_404_for_missing_target(api_db_session):
    user = _user(api_db_session)
    app.dependency_overrides[get_db] = _override_db(api_db_session)
    client = TestClient(app)

    try:
        response = client.post(f"/crawl/{uuid.uuid4()}?user_id={user.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Crawl target not found"}


def test_target_crawl_queues_job(api_db_session, monkeypatch):
    user = _user(api_db_session)
    queued_job_ids = []

    def fake_run_queued_target_crawl(job_id):
        queued_job_ids.append(job_id)

    monkeypatch.setattr(api_app, "run_queued_target_crawl", fake_run_queued_target_crawl)

    target = CrawlTarget(
        user_id=user.id,
        base_url="https://example.com",
        crawl_mode="static",
    )
    api_db_session.add(target)
    api_db_session.flush()

    app.dependency_overrides[get_db] = _override_db(api_db_session)
    client = TestClient(app)

    try:
        response = client.post(f"/crawl/{target.id}?user_id={user.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    body = response.json()
    assert body["target_id"] == str(target.id)
    assert body["target_url"] == "https://example.com"
    assert body["status"] == "pending"
    assert queued_job_ids == [uuid.UUID(body["id"])]


def test_crawl_queues_all_active_targets(api_db_session, monkeypatch):
    user = _user(api_db_session)
    queued_job_ids = []

    def fake_run_queued_target_crawl(job_id):
        queued_job_ids.append(job_id)

    monkeypatch.setattr(api_app, "run_queued_target_crawl", fake_run_queued_target_crawl)

    active_target = CrawlTarget(
        user_id=user.id,
        base_url="https://example.com",
        crawl_mode="static",
    )
    inactive_target = CrawlTarget(
        user_id=user.id,
        base_url="https://inactive.example.com",
        crawl_mode="static",
        is_active=False,
    )
    api_db_session.add_all([active_target, inactive_target])
    api_db_session.flush()

    app.dependency_overrides[get_db] = _override_db(api_db_session)
    client = TestClient(app)

    try:
        response = client.post("/crawl", json={"user_id": str(user.id)})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    body = response.json()
    assert body["user_id"] == str(user.id)
    assert body["targets_queued"] == 1
    assert len(body["job_ids"]) == 1
    assert queued_job_ids == [uuid.UUID(body["job_ids"][0])]


def test_list_crawl_jobs(api_db_session):
    user = _user(api_db_session)
    target = CrawlTarget(
        user_id=user.id,
        base_url="https://example.com",
        crawl_mode="static",
    )
    api_db_session.add(target)
    api_db_session.flush()
    job = CrawlJob(
        user_id=user.id,
        target_id=target.id,
        target_url="https://example.com/page",
    )
    api_db_session.add(job)
    api_db_session.flush()

    app.dependency_overrides[get_db] = _override_db(api_db_session)
    client = TestClient(app)

    try:
        response = client.get(f"/crawl-jobs?user_id={user.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(job.id)
    assert response.json()[0]["target_url"] == "https://example.com/page"
    assert response.json()[0]["status"] == "pending"


def test_crawl_rejects_missing_internal_api_key(api_db_session, monkeypatch):
    user = _user(api_db_session)
    monkeypatch.setattr(settings, "BACKEND_API_TOKEN", "secret")
    app.dependency_overrides[get_db] = _override_db(api_db_session)
    client = TestClient(app)

    try:
        response = client.post("/crawl", json={"user_id": str(user.id)})
    finally:
        app.dependency_overrides.clear()
        monkeypatch.setattr(settings, "BACKEND_API_TOKEN", None)

    assert response.status_code == 401


def test_scheduler_tick_requires_internal_api_key(api_db_session, monkeypatch):
    monkeypatch.setattr(settings, "BACKEND_API_TOKEN", "secret")
    app.dependency_overrides[get_db] = _override_db(api_db_session)
    client = TestClient(app)

    try:
        response = client.post("/scheduler/tick")
    finally:
        app.dependency_overrides.clear()
        monkeypatch.setattr(settings, "BACKEND_API_TOKEN", None)

    assert response.status_code == 401


def test_scheduler_tick_queues_due_targets(api_db_session, monkeypatch):
    user = _user(api_db_session)
    queued_job_ids = []

    def fake_run_queued_target_crawl(job_id):
        queued_job_ids.append(job_id)

    monkeypatch.setattr(api_app, "run_queued_target_crawl", fake_run_queued_target_crawl)

    target = CrawlTarget(
        user_id=user.id,
        base_url="https://example.com",
        crawl_mode="static",
        schedule_enabled=True,
        schedule_config={"type": "interval", "value": 1, "unit": "hours"},
        schedule_timezone="Asia/Tokyo",
        next_run_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    api_db_session.add(target)
    api_db_session.flush()

    app.dependency_overrides[get_db] = _override_db(api_db_session)
    client = TestClient(app)

    try:
        response = client.post("/scheduler/tick")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    body = response.json()
    assert body["targets_checked"] == 1
    assert body["targets_queued"] == 1
    assert len(body["job_ids"]) == 1
    assert queued_job_ids == [uuid.UUID(body["job_ids"][0])]


def test_target_crawl_cannot_use_another_users_target(api_db_session):
    owner = _user(api_db_session, "owner@example.com")
    other = _user(api_db_session, "other@example.com")
    target = CrawlTarget(
        user_id=owner.id,
        base_url="https://example.com",
        crawl_mode="static",
    )
    api_db_session.add(target)
    api_db_session.flush()

    app.dependency_overrides[get_db] = _override_db(api_db_session)
    client = TestClient(app)

    try:
        response = client.post(f"/crawl/{target.id}?user_id={other.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_invite_verify_endpoint_accepts_valid_code(api_db_session):
    _, code = create_invite(
        api_db_session,
        email="user@example.com",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    app.dependency_overrides[get_db] = _override_db(api_db_session)
    client = TestClient(app)

    try:
        response = client.post(
            "/auth/invites/verify",
            json={"email": "user@example.com", "access_code": code},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_invite_verify_endpoint_rejects_invalid_code(api_db_session):
    create_invite(
        api_db_session,
        email="user@example.com",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    app.dependency_overrides[get_db] = _override_db(api_db_session)
    client = TestClient(app)

    try:
        response = client.post(
            "/auth/invites/verify",
            json={"email": "user@example.com", "access_code": "wrong"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
