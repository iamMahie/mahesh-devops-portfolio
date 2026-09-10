"""Server-rendered admin shell and HttpOnly browser authentication."""

from __future__ import annotations

import secrets

import jwt
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError

from app.api.deps import (
    ADMIN_COOKIE,
    AuthServiceDep,
    browser_csrf,
    validate_browser_csrf,
)
from app.core.config import settings
from app.core.exceptions import AppError, AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token
from app.models.admin import AdminUser
from app.models.enums import BookingStatus, InquiryStatus
from app.schemas.auth import LoginRequest
from app.web.templates import templates

router = APIRouter(prefix="/admin", include_in_schema=False)
LOGIN_COOKIE = "wed_admin_login"
PRIVATE_HEADERS = {"Cache-Control": "no-store", "Referrer-Policy": "same-origin"}
SECTIONS = {
    "overview": ("Studio overview", "The work to publish. The conversations to follow up."),
    "inquiries": ("Enquiries", "Follow each conversation from first hello to a decision."),
    "bookings": ("Consultations", "Manage requests. Confirm a time with the customer before confirming here."),
    "messages": ("Messages", "Read and organise messages sent through the contact form."),
    "portfolios": ("Portfolios", "Publish real collections and manage their gallery photographs."),
}


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303, headers=PRIVATE_HEADERS)


def _login_page(
    request: Request, *, email: str = "", error: str = "", status_code: int = 200,
) -> HTMLResponse:
    nonce = secrets.token_urlsafe(32)
    response = templates.TemplateResponse(
        request, "admin/login.html",
        {"email": email, "error": error, "csrf": browser_csrf(nonce, purpose="login")},
        status_code=status_code, headers=PRIVATE_HEADERS,
    )
    response.set_cookie(
        LOGIN_COOKIE, nonce, max_age=900, path="/admin", httponly=True,
        secure=settings.is_production, samesite="strict",
    )
    return response


async def _browser_admin(request: Request, auth: AuthServiceDep) -> AdminUser | None:
    token = request.cookies.get(ADMIN_COOKIE)
    if not token:
        return None
    try:
        return await auth.resolve_token(token)
    except (AuthenticationError, PermissionDeniedError):
        return None


@router.get("/login", response_class=HTMLResponse, response_model=None, name="admin_login")
async def login_page(request: Request, auth: AuthServiceDep) -> HTMLResponse | RedirectResponse:
    if await _browser_admin(request, auth):
        return _redirect("/admin")
    response = _login_page(request)
    response.delete_cookie(ADMIN_COOKIE, path="/")
    return response


@router.post("/login", response_class=HTMLResponse, response_model=None, name="admin_login_submit")
async def login(request: Request, auth: AuthServiceDep) -> HTMLResponse | RedirectResponse:
    form = await request.form()
    email = form.get("email", "")
    email = email.strip()[:254] if isinstance(email, str) else ""
    password = form.get("password", "")
    submitted = form.get("csrf", "")
    try:
        validate_browser_csrf(
            request.cookies.get(LOGIN_COOKIE, ""),
            submitted if isinstance(submitted, str) else None,
            purpose="login",
        )
    except PermissionDeniedError as exc:
        return _login_page(request, email=email, error=exc.message, status_code=403)
    try:
        payload = LoginRequest(email=email, password=password)
    except ValidationError:
        return _login_page(
            request, email=email, error="Enter a valid email and a password of 8–128 characters.",
            status_code=422,
        )
    try:
        result = await auth.login(str(payload.email).lower(), payload.password)
    except AppError as exc:
        return _login_page(request, email=email, error=exc.message, status_code=exc.status_code)
    claims = decode_access_token(result.access_token)
    # Independent logins must not share a CSRF token, even within the same second.
    claims["jti"] = secrets.token_urlsafe(32)
    token = jwt.encode(claims, settings.secret_key, algorithm=settings.algorithm)
    response = _redirect("/admin")
    response.set_cookie(
        ADMIN_COOKIE, token, max_age=result.expires_in, path="/",
        httponly=True, secure=settings.is_production, samesite="lax",
    )
    response.delete_cookie(LOGIN_COOKIE, path="/admin")
    return response


@router.post("/logout", response_model=None, name="admin_logout")
async def logout(request: Request) -> HTMLResponse | RedirectResponse:
    form = await request.form()
    submitted = form.get("csrf", "")
    try:
        validate_browser_csrf(
            request.cookies.get(ADMIN_COOKIE, ""),
            submitted if isinstance(submitted, str) else None,
        )
    except PermissionDeniedError as exc:
        return templates.TemplateResponse(
            request, "admin/session_error.html", {"error": exc.message},
            status_code=403, headers=PRIVATE_HEADERS,
        )
    response = _redirect("/admin/login")
    response.delete_cookie(ADMIN_COOKIE, path="/", httponly=True, secure=settings.is_production, samesite="lax")
    response.delete_cookie(LOGIN_COOKIE, path="/admin")
    return response


@router.get("", response_class=HTMLResponse, response_model=None, name="admin_dashboard")
@router.get("/inquiries", response_class=HTMLResponse, response_model=None, name="admin_inquiries")
@router.get("/bookings", response_class=HTMLResponse, response_model=None, name="admin_bookings")
@router.get("/messages", response_class=HTMLResponse, response_model=None, name="admin_messages")
@router.get("/portfolios", response_class=HTMLResponse, response_model=None, name="admin_portfolios")
async def workspace(request: Request, auth: AuthServiceDep) -> HTMLResponse | RedirectResponse:
    admin = await _browser_admin(request, auth)
    if admin is None:
        response = _redirect("/admin/login")
        response.delete_cookie(ADMIN_COOKIE, path="/")
        return response
    section = request.url.path.rsplit("/", 1)[-1]
    section = section if section in SECTIONS else "overview"
    heading, description = SECTIONS[section]
    return templates.TemplateResponse(
        request, "admin/dashboard.html", {
            "admin": admin, "section": section, "heading": heading, "description": description,
            "sections": SECTIONS, "api_prefix": settings.api_v1_prefix,
            "csrf": browser_csrf(request.cookies[ADMIN_COOKIE]),
            "inquiry_statuses": list(InquiryStatus), "booking_statuses": list(BookingStatus),
            "page_size": min(20, settings.max_page_size),
        },
        headers=PRIVATE_HEADERS,
    )
