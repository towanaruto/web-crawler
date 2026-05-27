from datetime import datetime, timedelta, timezone

from src.auth.invites import consume_verified_invite, create_invite, verify_invite


def test_verify_invite_accepts_correct_code(db_session):
    _, code = create_invite(
        db_session,
        email="User@Example.com",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    invite = verify_invite(
        db_session,
        email="user@example.com",
        access_code=code,
    )

    assert invite is not None
    assert invite.verified_at is not None


def test_verify_invite_rejects_wrong_email(db_session):
    _, code = create_invite(
        db_session,
        email="user@example.com",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    invite = verify_invite(
        db_session,
        email="other@example.com",
        access_code=code,
    )

    assert invite is None


def test_consume_requires_verified_invite(db_session):
    create_invite(
        db_session,
        email="user@example.com",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    invite = consume_verified_invite(
        db_session,
        email="user@example.com",
        auth0_sub="google-oauth2|123",
    )

    assert invite is None


def test_consume_marks_invite_used(db_session):
    _, code = create_invite(
        db_session,
        email="user@example.com",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    verify_invite(db_session, email="user@example.com", access_code=code)

    invite = consume_verified_invite(
        db_session,
        email="user@example.com",
        auth0_sub="google-oauth2|123",
    )

    assert invite is not None
    assert invite.used_at is not None
    assert invite.used_by_auth0_sub == "google-oauth2|123"
