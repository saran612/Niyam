"""Authentication, password hashing, and token helpers."""

from datetime import timedelta
from typing import Any

import jwt
from app.core.clock import clock
from app.core.config import settings
from app.models.entities import RoleEnum, User
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from pydantic import BaseModel

ph = PasswordHasher()


class TokenPayload(BaseModel):
    sub: str
    email: str
    role: RoleEnum
    region_id: int | None = None
    institution_id: int | None = None
    exp: int


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def create_access_token(user: User) -> str:
    now_ts = clock.now()
    exp_ts = now_ts + timedelta(minutes=settings.JWT_EXPIRES_MINUTES)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "region_id": user.region_id,
        "institution_id": user.institution_id,
        "exp": int(exp_ts.timestamp()),
        "iat": int(now_ts.timestamp()),
    }
    encoded = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return str(encoded)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        # Decode and verify signature, skipping system-clock exp/iat validation
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub"], "verify_exp": False, "verify_iat": False},
        )
        # Validate expiration deterministically against virtual clock
        now_epoch = int(clock.now().timestamp())
        if payload.get("exp", 0) < now_epoch:
            return None
        return payload
    except jwt.PyJWTError:
        return None

