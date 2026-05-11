import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Annotated
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
import redis.asyncio as aioredis

from ..db import get_db
from ..config import settings
from ..redis_client import get_redis

from ..schemas import SignUp, Login, TokenResponse, MeResponse
from ..models import Users

from ..encryption import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from ..logging_config import request_id_var

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer()

db_dependency = Annotated[AsyncSession, Depends(get_db)]
redis_dependency = Annotated[aioredis.Redis, Depends(get_redis)]


async def _set_request_id(x_request_id: Annotated[str, Header()] = "-") -> None:
    request_id_var.set(x_request_id)


router = APIRouter(
    prefix="/auth", tags=["auth"], dependencies=[Depends(_set_request_id)]
)


async def _create_user(form: SignUp, role: str, db: db_dependency):
    logger.info(
        "Attempt at creating user", extra={"event": "user_create", "status": "attempt"}
    )
    result = await db.execute(select(Users).where(Users.email == form.email))
    scalar = result.scalar_one_or_none()

    if scalar:
        logger.info(
            "Email already in system",
            extra={"event": "user_create", "status": "conflict"},
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    new_user = Users(
        id=str(uuid4()),
        name=form.name,
        role=role,
        email=form.email,
        password_hash=hash_password(form.password),
    )

    db.add(new_user)
    try:
        await db.commit()
    except Exception as exc:
        logger.error(
            "Failed to create user",
            extra={"event": "user_create", "status": "error", "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user",
        )
    logger.info(
        "User created successfully", extra={"event": "user_create", "status": "success"}
    )
    return {"detail": "User created successfully"}


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(body: SignUp, db: db_dependency):
    await _create_user(body, "user", db)


@router.post("/admin/register", status_code=status.HTTP_201_CREATED)
async def register_admin(body: SignUp, db: db_dependency):
    await _create_user(body, "admin", db)


@router.post("/login", status_code=status.HTTP_200_OK, response_model=TokenResponse)
async def login(body: Login, db: db_dependency):
    result = await db.execute(select(Users).where(Users.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        logger.warning(
            "Invalid credentials", extra={"event": "login", "status": "failure"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials."
        )

    access_token = create_access_token(
        name=user.name,
        email=user.email,
        role=user.role,
        user_id=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(
        name=user.name,
        email=user.email,
        role=user.role,
        user_id=user.id,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    logger.info("Login successful", extra={"event": "login", "status": "success"})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def _validate_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    redis: aioredis.Redis = Depends(get_redis),
) -> tuple[dict[str, Any], str]:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError as exc:
        logger.warning(
            "Token validation failed",
            extra={"event": "token_validate", "status": "failure", "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    is_revoked = await redis.get(f"blacklist:{token}")
    if is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked"
        )

    return payload, token


async def _blacklist_token(
    token: str, payload: dict[str, Any], redis: aioredis.Redis
) -> None:
    exp = payload.get("exp")
    if not isinstance(exp, (int, float)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
    await redis.setex(f"blacklist:{token}", ttl, "1")


@router.post("/refresh", status_code=status.HTTP_200_OK, response_model=TokenResponse)
async def refresh(
    db: db_dependency,
    redis: redis_dependency,
    x_refresh_token: Annotated[str, Header()],
    token_context: tuple[dict[str, Any], str] = Depends(_validate_bearer_token),
):
    payload, access_token = token_context

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expected access token in Authorization header",
        )

    try:
        refresh_payload = decode_token(x_refresh_token)
    except JWTError as exc:
        logger.warning(
            "Refresh token validation failed",
            extra={"event": "refresh", "status": "failure", "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    if refresh_payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expected refresh token in X-Refresh-Token header",
        )

    is_revoked = await redis.get(f"blacklist:{x_refresh_token}")
    if is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked"
        )

    if refresh_payload.get("sub") != payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token subject mismatch"
        )

    result = await db.execute(select(Users).where(Users.id == refresh_payload["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    await _blacklist_token(access_token, payload, redis)

    new_access_token = create_access_token(
        name=user.name,
        email=user.email,
        role=user.role,
        user_id=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    logger.info("Token refreshed", extra={"event": "refresh", "status": "success"})
    return TokenResponse(access_token=new_access_token, refresh_token=x_refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    redis: redis_dependency,
    x_refresh_token: Annotated[str, Header()],
    token_context: tuple[dict[str, Any], str] = Depends(_validate_bearer_token),
):
    payload, token = token_context
    await _blacklist_token(token, payload, redis)

    try:
        refresh_payload = decode_token(x_refresh_token)
        if refresh_payload.get("type") == "refresh":
            await _blacklist_token(x_refresh_token, refresh_payload, redis)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Expected refresh token in X-Refresh-Token header",
            )
    except JWTError as exc:
        logger.warning(
            "Refresh token validation failed during logout",
            extra={"event": "logout", "status": "failure", "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    logger.info("Logout successful", extra={"event": "logout", "status": "success"})
    return {"detail": "Logged out successfully"}


@router.get("/me", status_code=status.HTTP_200_OK, response_model=MeResponse)
async def me(
    db: db_dependency,
    token_context: tuple[dict[str, Any], str] = Depends(_validate_bearer_token),
):
    payload, _ = token_context

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Expected access token"
        )

    result = await db.execute(select(Users).where(Users.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User not found"
        )

    return MeResponse(name=user.name, email=user.email, role=user.role)
