"""Regular HTML forms for content management; no JavaScript is required to save."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from starlette.datastructures import FormData

from app.api.deps import ADMIN_COOKIE, ContentServiceDep, PaginationDep, browser_csrf, validate_browser_csrf
from app.core.config import settings
from app.core.exceptions import PermissionDeniedError
from app.models.admin import AdminUser
from app.schemas.content import ReelInput, SiteContentInput
from app.web.admin import PRIVATE_HEADERS, SECTIONS, _browser_admin, _redirect
from app.web.templates import templates

router = APIRouter(prefix="/admin/content", include_in_schema=False)
BrowserAdmin = Annotated[AdminUser | None, Depends(_browser_admin)]


async def content_page(
    request: Request, admin: AdminUser, service: ContentServiceDep, pagination: PaginationDep,
    *, edit: int | None = None, values: dict | None = None, errors: dict | None = None,
    area: str = "", status_code: int = 200,
) -> HTMLResponse:
    reel = await service.get_reel(edit) if edit is not None else None
    details = await service.business()
    return templates.TemplateResponse(
        request, "admin/content.html", {
            "admin": admin, "section": "content", "sections": SECTIONS,
            "api_prefix": settings.api_v1_prefix, "page_size": pagination.size,
            "csrf": browser_csrf(request.cookies[ADMIN_COOKIE]),
            "details": values if area == "details" else details,
            "reel": values if area == "reel" else (
                ReelInput.model_validate(reel).model_dump() if reel else ReelInput.model_construct(
                    title="", video_url="", poster_url="",
                ).model_dump()
            ),
            "edit": edit, "errors": errors or {}, "area": area,
            "reel_page": await service.list_reels(pagination),
            "saved": request.query_params.get("saved") in {"details", "reel", "deleted"},
        }, status_code=status_code, headers=PRIVATE_HEADERS,
    )


def form_values(form: FormData, model: type[ReelInput] | type[SiteContentInput]) -> dict:
    values = {}
    for name in model.model_fields:
        value = form.get(name, "")
        values[name] = value if isinstance(value, str) else ""
    if model is ReelInput:
        values["is_published"] = form.get("is_published") == "on"
    return values


def check_csrf(request: Request, form: FormData) -> HTMLResponse | None:
    submitted = form.get("csrf")
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
    return None


@router.get("", response_model=None)
async def content(
    request: Request, admin: BrowserAdmin, service: ContentServiceDep, pagination: PaginationDep,
    edit: Annotated[int | None, Query(gt=0)] = None,
) -> HTMLResponse | RedirectResponse:
    if admin is None:
        return _redirect("/admin/login")
    return await content_page(request, admin, service, pagination, edit=edit)


@router.post("/details", response_model=None)
async def save_details(
    request: Request, admin: BrowserAdmin, service: ContentServiceDep, pagination: PaginationDep,
) -> HTMLResponse | RedirectResponse:
    if admin is None:
        return _redirect("/admin/login")
    form = await request.form()
    if error := check_csrf(request, form):
        return error
    values = form_values(form, SiteContentInput)
    try:
        payload = SiteContentInput.model_validate(values)
    except ValidationError as exc:
        errors = {str(item["loc"][0]): item["msg"].removeprefix("Value error, ") for item in exc.errors()}
        return await content_page(
            request, admin, service, pagination, values=values, errors=errors,
            area="details", status_code=422,
        )
    await service.save_details(payload)
    return _redirect("/admin/content?saved=details")


@router.post("/reels", response_model=None)
async def save_reel(
    request: Request, admin: BrowserAdmin, service: ContentServiceDep, pagination: PaginationDep,
    edit: Annotated[int | None, Query(gt=0)] = None,
) -> HTMLResponse | RedirectResponse:
    if admin is None:
        return _redirect("/admin/login")
    form = await request.form()
    if error := check_csrf(request, form):
        return error
    values = form_values(form, ReelInput)
    try:
        payload = ReelInput.model_validate(values)
    except ValidationError as exc:
        errors = {str(item["loc"][0]): item["msg"].removeprefix("Value error, ") for item in exc.errors()}
        return await content_page(
            request, admin, service, pagination, edit=edit, values=values, errors=errors,
            area="reel", status_code=422,
        )
    await service.save_reel(payload, edit)
    return _redirect("/admin/content?saved=reel#films")


@router.post("/reels/{reel_id}/delete", response_model=None)
async def delete_reel(
    request: Request, admin: BrowserAdmin, service: ContentServiceDep,
    reel_id: Annotated[int, Path(gt=0)],
) -> HTMLResponse | RedirectResponse:
    if admin is None:
        return _redirect("/admin/login")
    form = await request.form()
    if error := check_csrf(request, form):
        return error
    if form.get("confirm") != "yes":
        return templates.TemplateResponse(
            request, "admin/session_error.html",
            {"error": "Nothing was deleted. Return to Website content and confirm the film to remove."},
            status_code=422, headers=PRIVATE_HEADERS,
        )
    await service.delete_reel(reel_id)
    return _redirect("/admin/content?saved=deleted#films")
