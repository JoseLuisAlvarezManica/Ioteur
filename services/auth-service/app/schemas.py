from pydantic import BaseModel, EmailStr


class SignUp(BaseModel):
    name: str
    email: str
    password: str


class Login(BaseModel):
    email: str
    password: str


class Logout(BaseModel):
    pass


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
