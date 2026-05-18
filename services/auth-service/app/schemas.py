# Esquema para actualización de usuario (PUT)
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None


class SignUp(BaseModel):
    name: str
    email: str
    password: str


class Login(BaseModel):
    email: str
    password: str


class User(BaseModel):
    username: str
    email: EmailStr
    role: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class RefreshRequest(BaseModel):
    access_token: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    name: str
    email: EmailStr
    role: str


class UserIdResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
