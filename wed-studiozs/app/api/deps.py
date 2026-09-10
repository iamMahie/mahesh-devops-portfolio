"""Shared FastAPI dependencies: DB session, services, pagination, current admin."""

from __future__ import annotations

import hashlib
import hmac
from typing import Annotated

from fastapi import Depends, Query, Request, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.pagination import PaginationParams
from app.db.session import get_session
from app.models.admin import AdminUser
from app.services.auth import AuthService
from app.services.crm import BookingService, ContactService, InquiryService
from app.services.portfolio import GalleryService, PortfolioService

SessionDep = Annotated[AsyncSession, Depends(get_session)]

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/token", auto_error=False
)


def get_pagination(
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    size: Annotated[int, Query(ge=1, le=settings.max_page_size)] = settings.default_page_size,
) -> PaginationParams:
    return PaginationParams(page=page, size=size)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination)]


# ------------------------------------------------------------------ services
def get_portfolio_service(session: SessionDep) -> PortfolioService:
    return PortfolioService(session)


def get_gallery_service(session: SessionDep) -> GalleryService:
    return GalleryService(session)


def get_inquiry_service(session: SessionDep) -> InquiryService:
    return InquiryService(session)


def get_booking_service(session: SessionDep) -> BookingService:
    return BookingService(session)


def get_contact_service(session: SessionDep) -> ContactService:
    return ContactService(session)


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)


PortfolioServiceDep = Annotated[PortfolioService, Depends(get_portfolio_service)]
GalleryServiceDep = Annotated[GalleryService, Depends(get_gallery_service)]
InquiryServiceDep = Annotated[InquiryService, Depends(get_inquiry_service)]
BookingServiceDep = Annotated[BookingService, Depends(get_booking_service)]
ContactServiceDep = Annotated[ContactService, Depends(get_contact_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


# ---------------------------------------------------------------- current user
ADMIN_COOKIE = "wed_admin_session"
CSRF_HEADER = "X-CSRF-Token"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def browser_csrf(token: str, *, purpose: str = "session") -> str:
    """Bind a non-credential form/header token to one browser session."""
    return hmac.new(
        settings.secret_key.encode(),
        f"wed-admin:{purpose}:{token}".encode(),
        hashlib.sha256,
    ).hexdigest()


def validate_browser_csrf(
    token: str, submitted: str | None, *, purpose: str = "session",
) -> None:
    if (
        not token or not submitted or len(submitted) != 64
        or any(character not in "0123456789abcdef" for character in submitted)
        or not hmac.compare_digest(browser_csrf(token, purpose=purpose), submitted)
    ):
        raise PermissionDeniedError("Your security check expired. Reload the page and try again.")


async def get_current_admin(
    request: Request,
    response: Response,
    auth_service: AuthServiceDep,
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
) -> AdminUser:
    # An explicitly supplied Authorization header always owns authentication.
    # Never silently turn a failed API credential into a browser session.
    if request.headers.get("Authorization") is not None:
        if not token:
            raise AuthenticationError("Not authenticated.")
        return await auth_service.resolve_token(token)
    cookie = request.cookies.get(ADMIN_COOKIE)
    if not cookie:
        raise AuthenticationError("Not authenticated.")
    try:
        admin = await auth_service.resolve_token(cookie)
    except PermissionDeniedError as exc:
        raise AuthenticationError("Your admin session is no longer available.") from exc
    if request.method not in SAFE_METHODS:
        validate_browser_csrf(cookie, request.headers.get(CSRF_HEADER))
    response.headers["Cache-Control"] = "no-store"
    return admin


CurrentAdmin = Annotated[AdminUser, Depends(get_current_admin)]
