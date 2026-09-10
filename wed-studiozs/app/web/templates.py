"""Jinja2 environment shared by every server-rendered page."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.models.enums import PortfolioCategory

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Values available to every template without passing them per-view.
templates.env.globals.update(
    business={
        "name": settings.app_name,
        "phone": settings.business_phone,
        "email": settings.business_email,
        "address": settings.business_address,
    },
    categories=list(PortfolioCategory),
    current_year=date.today().year,
)
