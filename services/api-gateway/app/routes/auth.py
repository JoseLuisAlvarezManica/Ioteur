import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query

from ..decorators import must_be_admin, must_be_logged_in, bearer_scheme
from ..helpers.auth_client import AuthClient, get_auth_client
from ..schemas import (
    SignUp,
    Login,
    TokenResponse,
    MeResponse,
    UserUpdate,
    UserSelfUpdate,
    UserIdResponse,
    UsersPageResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

auth_dependency = Annotated[AuthClient, Depends(get_auth_client)]


# --- Usuarios ---


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(body: SignUp, auth_client: auth_dependency):
    code, data = await auth_client.post("/auth/signup", body.model_dump())
    if code != status.HTTP_201_CREATED:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.post("/admin/register", status_code=status.HTTP_201_CREATED)
@must_be_admin
async def register_admin(request: Request, body: SignUp, auth_client: auth_dependency):
    code, data = await auth_client.post(
        "/auth/admin/register", body.model_dump(), headers=request.state.auth_headers
    )
    if code != status.HTTP_201_CREATED:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.get(
    "/user/",
    status_code=status.HTTP_200_OK,
    response_model=UsersPageResponse,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_admin
async def get_all_users(
    request: Request,
    auth_client: auth_dependency,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
):
    code, data = await auth_client.get(
        f"/auth/user/?page={page}&page_size={page_size}",
        headers=request.state.auth_headers,
    )
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.get(
    "/user/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserIdResponse,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_admin
async def get_user_by_id(user_id: str, request: Request, auth_client: auth_dependency):
    code, data = await auth_client.get(
        f"/auth/user/{user_id}", headers=request.state.auth_headers
    )
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.get(
    "/user/by-email/{email}",
    status_code=status.HTTP_200_OK,
    response_model=UserIdResponse,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_admin
async def get_user_by_email(email: str, request: Request, auth_client: auth_dependency):
    code, data = await auth_client.get(
        f"/auth/user/by-email/{email}", headers=request.state.auth_headers
    )
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.put(
    "/user/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_admin
async def update_user(
    user_id: str, request: Request, body: UserUpdate, auth_client: auth_dependency
):
    code, data = await auth_client.put(
        f"/auth/user/{user_id}",
        body.model_dump(exclude_none=True),
        headers=request.state.auth_headers,
    )
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.delete(
    "/user/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_admin
async def delete_user(user_id: str, request: Request, auth_client: auth_dependency):
    code, data = await auth_client.delete(
        f"/auth/user/{user_id}", headers=request.state.auth_headers
    )
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data


# --- Autenticación ---


@router.post("/login", status_code=status.HTTP_200_OK, response_model=TokenResponse)
async def login(body: Login, auth_client: auth_dependency):
    code, data = await auth_client.post("/auth/login", body.model_dump())
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_logged_in
async def refresh(request: Request, auth_client: auth_dependency):
    x_refresh_token = request.headers.get("x-refresh-token")
    if not x_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Refresh-Token header requerido",
        )
    headers = {**request.state.auth_headers, "x-refresh-token": x_refresh_token}
    code, data = await auth_client.post("/auth/refresh", {}, headers=headers)
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_logged_in
async def logout(request: Request, auth_client: auth_dependency):
    x_refresh_token = request.headers.get("x-refresh-token")
    if not x_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Refresh-Token header requerido",
        )
    headers = {**request.state.auth_headers, "x-refresh-token": x_refresh_token}
    code, data = await auth_client.post("/auth/logout", {}, headers=headers)
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=MeResponse,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_logged_in
async def me(request: Request, auth_client: auth_dependency):
    code, data = await auth_client.get("/auth/me", headers=request.state.auth_headers)
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.patch(
    "/me",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_logged_in
async def update_me(
    request: Request, body: UserSelfUpdate, auth_client: auth_dependency
):
    code, data = await auth_client.patch(
        "/auth/me",
        body.model_dump(exclude_none=True),
        headers=request.state.auth_headers,
    )
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data
