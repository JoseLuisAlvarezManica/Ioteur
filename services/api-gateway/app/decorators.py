from functools import wraps

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from jose import jwt, JWTError

from .config import settings
from .redis_client import get_redis


ALGORITHM = "RS256"


def _wrap_pem(pem: str, key_type: str) -> str:
    header = f"-----BEGIN {key_type}-----"
    footer = f"-----END {key_type}-----"
    pem = pem.strip().replace("\r", "")
    if not pem.startswith(header):
        pem = f"{header}\n{pem}"
    if not pem.endswith(footer):
        pem = f"{pem}\n{footer}"
    return pem


def must_be_logged_in(route):
    @wraps(route)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request")
        if request is None or not isinstance(request, Request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Petición invalida.",
            )

        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Formato de encabezado de autorización inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )

        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Formato de encabezado de autorización inválido",
            )

        token = parts[1]
        try:
            public_key = _wrap_pem(settings.PUBLIC_KEY, "PUBLIC KEY")
            payload = jwt.decode(token, public_key, algorithms=[ALGORITHM])
            username = payload.get("sub")
            phone_number = payload.get("phone_number")
            role = payload.get("role")
            request.state.auth_headers = {"Authorization": authorization}
            request.state.username = username
            request.state.phone_number = phone_number
            request.state.role = role
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El token no es válido",
            )

        redis = get_redis()
        is_revoked = await redis.get(f"blacklist:{token}")
        if is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El token ha sido revocado",
            )

        refresh_token = request.headers.get("x-refresh-token")
        if refresh_token:
            is_refresh_revoked = await redis.get(f"blacklist:{refresh_token}")
            if is_refresh_revoked:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="El refresh token ha sido revocado",
                )

        return await route(*args, **kwargs)

    return wrapper


def must_be_admin(route):
    @wraps(route)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request")
        if request is None or not isinstance(request, Request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Petición invalida."
            )

        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Formato de encabezado de autorización inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )

        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Formato de encabezado de autorización inválido",
            )

        token = parts[1]
        try:
            public_key = _wrap_pem(settings.PUBLIC_KEY, "PUBLIC KEY")
            payload = jwt.decode(token, public_key, algorithms=[ALGORITHM])
            username = payload.get("sub")
            phone_number = payload.get("phone_number")
            role = payload.get("role")
            request.state.auth_headers = {"Authorization": authorization}
            request.state.username = username
            request.state.phone_number = phone_number
            request.state.role = role
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El token no es válido",
            )

        redis = get_redis()
        is_revoked = await redis.get(f"blacklist:{token}")
        if is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El token ha sido revocado",
            )

        refresh_token = request.headers.get("x-refresh-token")
        if refresh_token:
            is_refresh_revoked = await redis.get(f"blacklist:{refresh_token}")
            if is_refresh_revoked:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="El refresh token ha sido revocado",
                )

        if role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fallo de permisos.",
            )
        return await route(*args, **kwargs)

    return wrapper


bearer_scheme = HTTPBearer()
