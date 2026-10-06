"""Jinja2 environment shared by every server-rendered page."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi.templating import Jinja2Templates

from fastapi import Request
from app.models.enums import PortfolioCategory
from app.services.content import default_business

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

def public_context(request: Request) -> dict[str, dict[str, str]]:
    return {"business": getattr(request.state, "business", default_business())}


templates = Jinja2Templates(directory=str(TEMPLATES_DIR), context_processors=[public_context])

# Values available to every template without passing them per-view.
templates.env.globals.update(
    categories=list(PortfolioCategory),
    current_year=date.today().year,
)
