from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt
from passlib.context import CryptContext
from .config import settings

ALGORITHM = "RS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    name: str, email: str, role: str, user_id: str, expires_delta: timedelta
) -> str:
    issued_at = datetime.now(timezone.utc)
    expires = issued_at + expires_delta
    payload = {
        "type": "access",
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": issued_at,
        "exp": expires,
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.PRIVATE_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    name: str, email: str, role: str, user_id: str, expires_delta: timedelta
) -> str:
    issued_at = datetime.now(timezone.utc)
    expires = issued_at + expires_delta
    payload = {
        "type": "refresh",
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": issued_at,
        "exp": expires,
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.PRIVATE_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.PUBLIC_KEY, algorithms=[ALGORITHM])
