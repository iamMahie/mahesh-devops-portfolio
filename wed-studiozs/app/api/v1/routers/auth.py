"""Login / token / current-admin endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import AuthServiceDep, CurrentAdmin
from app.core.exceptions import PermissionDeniedError
from app.schemas.auth import AdminCreate, AdminRead, LoginRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token, summary="Login with a JSON body")
async def login(payload: LoginRequest, auth_service: AuthServiceDep) -> Token:
    return await auth_service.login(payload.email, payload.password)


@router.post("/token", response_model=Token, summary="OAuth2 password flow (Swagger 'Authorize')")
async def login_form(
    auth_service: AuthServiceDep,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    return await auth_service.login(form.username, form.password)


@router.get("/me", response_model=AdminRead, summary="Current authenticated admin")
async def read_me(admin: CurrentAdmin) -> AdminRead:
    return AdminRead.model_validate(admin)


@router.post(
    "/admins",
    response_model=AdminRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create another admin (superuser only)",
)
async def create_admin(
    payload: AdminCreate,
    admin: CurrentAdmin,
    auth_service: AuthServiceDep,
) -> AdminRead:
    if not admin.is_superuser:
        raise PermissionDeniedError("Only superusers can create admin accounts.")
    return AdminRead.model_validate(await auth_service.register_admin(payload))
