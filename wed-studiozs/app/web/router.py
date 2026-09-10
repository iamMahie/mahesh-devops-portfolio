"""Public pages and progressively enhanced, post/redirect/get customer forms."""

from __future__ import annotations

from datetime import date
from typing import Annotated, TypeVar

from fastapi import APIRouter, Path, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, ValidationError

from app.api.deps import (
    BookingServiceDep,
    ContactServiceDep,
    InquiryServiceDep,
    PaginationDep,
    PortfolioServiceDep,
)
from app.core.exceptions import AppError, NotFoundError
from app.models.enums import PackageInterest, PortfolioCategory
from app.schemas.crm import BookingCreate, ContactMessageCreate, InquiryCreate
from app.web.admin import router as admin_router
from app.web.journal import STORIES, filter_stories, find_story
from app.web.receipts import Receipt, read_receipt, redirect_with_receipt
from app.web.templates import templates

router = APIRouter(include_in_schema=False)
router.include_router(admin_router)
FormModel = TypeVar("FormModel", bound=BaseModel)


def form_page(
    request: Request,
    template: str,
    *,
    values: dict[str, str] | None = None,
    errors: dict[str, str] | None = None,
    error: str | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request, template, {
            "values": values or {}, "errors": errors or {}, "error": error,
            "today": date.today().isoformat(), "packages": list(PackageInterest),
        },
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


async def parse_form(
    request: Request, model: type[FormModel],
) -> tuple[FormModel | None, dict[str, str], dict[str, str]]:
    form = await request.form()
    values = {
        name: value.strip() if isinstance(value := form.get(name, ""), str) else ""
        for name in model.model_fields
    }
    payload = {
        name: value if value or model.model_fields[name].is_required() else None
        for name, value in values.items()
    }
    try:
        return model.model_validate(payload), values, {}
    except ValidationError as exc:
        errors = {
            str(error["loc"][0]): error["msg"].removeprefix("Value error, ")
            for error in exc.errors()
        }
        return None, values, errors


@router.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request, service: PortfolioServiceDep) -> HTMLResponse:
    featured = await service.list_featured(limit=3)
    return templates.TemplateResponse(
        request, "index.html", {"featured": featured, "journal": STORIES}
    )


@router.get("/portfolios", response_class=HTMLResponse, name="portfolio_list")
async def portfolio_list(
    request: Request,
    service: PortfolioServiceDep,
    pagination: PaginationDep,
    category: Annotated[str, Query(max_length=30)] = "",
    q: Annotated[str, Query(max_length=100)] = "",
) -> HTMLResponse:
    try:
        active_category = PortfolioCategory(category) if category else None
    except ValueError as exc:
        raise NotFoundError("That photography category does not exist. Browse all our stories.") from exc
    query = q.strip()
    page = await service.list_portfolios(pagination, category=active_category, search=query or None)
    return templates.TemplateResponse(
        request, "portfolio_list.html", {
            "page": page, "active_category": active_category, "query": query,
            "journal": filter_stories(active_category, query),
        },
    )


@router.get("/portfolios/{slug}", response_class=HTMLResponse, name="portfolio_detail")
async def portfolio_detail(
    request: Request, service: PortfolioServiceDep, slug: Annotated[str, Path(min_length=1)],
) -> HTMLResponse:
    portfolio = await service.get_by_slug(slug)
    return templates.TemplateResponse(request, "portfolio_detail.html", {"portfolio": portfolio})


@router.get("/journal/{slug}", response_class=HTMLResponse, name="journal_detail")
async def journal_detail(request: Request, slug: str) -> HTMLResponse:
    story = find_story(slug)
    if story is None:
        raise NotFoundError("We could not find that story. There is more to explore in the journal.")
    return templates.TemplateResponse(
        request, "journal_detail.html",
        {"story": story, "related": [item for item in STORIES if item != story][:3]},
    )


@router.get("/inquiry", response_class=HTMLResponse, name="inquiry_form")
async def inquiry_form(request: Request) -> HTMLResponse:
    return form_page(request, "inquiry.html")


@router.post("/inquiry", response_class=HTMLResponse, response_model=None, name="inquiry_submit")
async def inquiry_submit(request: Request, service: InquiryServiceDep) -> HTMLResponse | RedirectResponse:
    payload, values, errors = await parse_form(request, InquiryCreate)
    if payload is None:
        return form_page(request, "inquiry.html", values=values, errors=errors, status_code=422)
    try:
        inquiry = await service.submit(payload)
    except AppError as exc:
        return form_page(
            request, "inquiry.html", values=values, error=exc.message, status_code=exc.status_code
        )
    return redirect_with_receipt(
        f"/inquiry/{inquiry.id}/thanks",
        Receipt(kind="inquiry", reference=inquiry.id, name=payload.customer_name),
    )


@router.get("/inquiry/{inquiry_id}/thanks", response_class=HTMLResponse, name="inquiry_thanks")
async def inquiry_thanks(
    request: Request, inquiry_id: Annotated[int, Path(gt=0)],
) -> HTMLResponse:
    receipt = read_receipt(request, "inquiry", inquiry_id)
    return templates.TemplateResponse(
        request, "inquiry_thanks.html", {
            "receipt": receipt, "heading": "Your enquiry is with the studio.",
            "message": "We have saved the details of your day. The studio will follow up using "
            "the contact details you shared. You do not need to submit the form again.",
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/booking", response_class=HTMLResponse, name="booking_form")
async def booking_form(request: Request) -> HTMLResponse:
    return form_page(request, "booking.html")


@router.post("/booking", response_class=HTMLResponse, response_model=None, name="booking_submit")
async def booking_submit(request: Request, service: BookingServiceDep) -> HTMLResponse | RedirectResponse:
    payload, values, errors = await parse_form(request, BookingCreate)
    if payload is None:
        return form_page(request, "booking.html", values=values, errors=errors, status_code=422)
    try:
        booking = await service.request(payload)
    except AppError as exc:
        return form_page(
            request, "booking.html", values=values, error=exc.message, status_code=exc.status_code
        )
    return redirect_with_receipt(
        "/booking/thanks", Receipt(
            kind="booking", reference=booking.id, name=payload.customer_name,
            date=payload.booking_date.isoformat(),
        ),
    )


@router.get("/booking/thanks", response_class=HTMLResponse, name="booking_thanks")
async def booking_thanks(request: Request) -> HTMLResponse:
    receipt = read_receipt(request, "booking")
    return templates.TemplateResponse(
        request, "inquiry_thanks.html", {
            "receipt": receipt, "heading": "Your consultation request is saved.",
            "message": "This is a request, not a confirmed appointment. "
            "The studio will follow up to find a time that works.",
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/contact", response_class=HTMLResponse, name="contact_page")
async def contact_page(request: Request) -> HTMLResponse:
    return form_page(request, "contact.html")


@router.post("/contact", response_class=HTMLResponse, response_model=None, name="contact_submit")
async def contact_submit(request: Request, service: ContactServiceDep) -> HTMLResponse | RedirectResponse:
    payload, values, errors = await parse_form(request, ContactMessageCreate)
    if payload is None:
        return form_page(request, "contact.html", values=values, errors=errors, status_code=422)
    try:
        message = await service.submit(payload)
    except AppError as exc:
        return form_page(
            request, "contact.html", values=values, error=exc.message, status_code=exc.status_code
        )
    return redirect_with_receipt(
        "/contact/thanks",
        Receipt(kind="contact", reference=message.id, name=payload.name),
    )


@router.get("/contact/thanks", response_class=HTMLResponse, name="contact_thanks")
async def contact_thanks(request: Request) -> HTMLResponse:
    receipt = read_receipt(request, "contact")
    return templates.TemplateResponse(
        request, "inquiry_thanks.html", {
            "receipt": receipt, "heading": "Message sent.",
            "message": "Your message is saved with the studio. We will reply using "
            "the email address you shared. There is no need to send it again.",
        },
        headers={"Cache-Control": "no-store"},
    )
