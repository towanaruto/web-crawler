from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.db.models import Invite, User

VERIFIED_INVITE_TTL = timedelta(minutes=15)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_invite_code(code: str) -> str:
    pepper = settings.INVITE_CODE_PEPPER or ""
    payload = f"{pepper}:{code.strip()}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def generate_invite_code() -> str:
    return secrets.token_urlsafe(32)


def verify_invite(db: Session, *, email: str, access_code: str) -> Invite | None:
    invite = _get_invite_by_code(db, access_code)
    if invite is None:
        return None
    now = datetime.now(timezone.utc)
    expires_at = _ensure_aware(invite.expires_at)
    if expires_at <= now or invite.used_at is not None:
        return None
    if normalize_email(invite.email) != normalize_email(email):
        return None

    invite.verified_at = now
    db.flush()
    return invite


def consume_verified_invite(
    db: Session,
    *,
    email: str,
    auth0_sub: str | None = None,
) -> Invite | None:
    email_norm = normalize_email(email)
    invite = db.scalar(
        select(Invite)
        .where(Invite.email == email_norm)
        .order_by(Invite.created_at.desc())
    )
    if invite is None:
        return None
    if invite.used_at is not None:
        if auth0_sub and invite.used_by_auth0_sub == auth0_sub:
            return invite
        return None
    now = datetime.now(timezone.utc)
    expires_at = _ensure_aware(invite.expires_at)
    verified_at = _ensure_aware(invite.verified_at) if invite.verified_at else None
    if expires_at <= now or verified_at is None:
        return None
    if verified_at + VERIFIED_INVITE_TTL <= now:
        return None

    invite.used_at = now
    invite.used_by_auth0_sub = auth0_sub
    db.flush()
    return invite


def attach_invite_to_user(db: Session, *, user: User) -> None:
    invite = db.scalar(
        select(Invite)
        .where(Invite.email == normalize_email(user.email))
        .order_by(Invite.created_at.desc())
    )
    if invite and invite.used_by_user_id is None:
        invite.used_by_user_id = user.id
        if invite.used_by_auth0_sub is None:
            invite.used_by_auth0_sub = user.auth0_sub
        db.flush()


def create_invite(
    db: Session,
    *,
    email: str,
    expires_at: datetime,
    access_code: str | None = None,
) -> tuple[Invite, str]:
    code = access_code or generate_invite_code()
    invite = Invite(
        email=normalize_email(email),
        code_hash=hash_invite_code(code),
        expires_at=expires_at,
    )
    db.add(invite)
    db.flush()
    return invite, code


def constant_time_code_equal(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)


def _get_invite_by_code(db: Session, access_code: str) -> Invite | None:
    candidate_hash = hash_invite_code(access_code)
    invite = db.scalar(select(Invite).where(Invite.code_hash == candidate_hash))
    if invite and constant_time_code_equal(invite.code_hash, candidate_hash):
        return invite
    return None


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
