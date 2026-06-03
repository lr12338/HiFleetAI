from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from backend.app.auth.dependencies import get_auth_service, get_current_principal
from backend.app.auth.service import AuthService, AuthenticatedPrincipal, InvalidCredentialsError


router = APIRouter(prefix="/auth", tags=["auth"])


class AuthUserResponse(BaseModel):
    username: str
    display_name: str
    role: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: AuthUserResponse


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    try:
        result = auth_service.login(username=payload.username, password=payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return LoginResponse(
        access_token=result.access_token,
        token_type=result.token_type,
        expires_in=result.expires_in,
        user=AuthUserResponse.model_validate(result.user),
    )


@router.get("/me", response_model=AuthUserResponse)
def me(
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> AuthUserResponse:
    return AuthUserResponse.model_validate(principal)
