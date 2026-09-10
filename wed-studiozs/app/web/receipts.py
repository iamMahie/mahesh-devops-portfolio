"""Short-lived, browser-bound confirmation pages without public customer records."""

from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt
from fastapi import Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings
from app.core.exceptions import NotFoundError

ReceiptKind = Literal["inquiry", "booking", "contact"]
_COOKIE = "ws_receipt"
_ISSUER = "wed-studiozs:receipts"


class Receipt(BaseModel):
    kind: ReceiptKind
    reference: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=150)
    date: str | None = None


def redirect_with_receipt(url: str, receipt: Receipt) -> RedirectResponse:
    now = datetime.now(UTC)
    token = jwt.encode(
        receipt.model_dump() | {
            "iss": _ISSUER,
            "iat": now,
            "exp": now + timedelta(minutes=10),
            "type": "receipt",
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    response = RedirectResponse(url, status_code=303, headers={"Cache-Control": "no-store"})
    response.set_cookie(
        _COOKIE, token, max_age=600, httponly=True, secure=settings.is_production,
        samesite="lax", path="/",
    )
    return response


def read_receipt(request: Request, kind: ReceiptKind, reference: int | None = None) -> Receipt:
    try:
        payload = jwt.decode(
            request.cookies.get(_COOKIE, ""),
            settings.secret_key,
            algorithms=[settings.algorithm],
            issuer=_ISSUER,
            options={"require": ["exp", "iat", "iss", "type", "kind", "reference", "name"]},
        )
        receipt = Receipt.model_validate(payload)
    except (jwt.InvalidTokenError, ValidationError) as exc:
        raise NotFoundError(
            "This confirmation has expired or belongs to another browser. "
            "Your submitted request is still saved; contact the studio if you need help."
        ) from exc
    if payload["type"] != "receipt" or receipt.kind != kind or (
        reference is not None and receipt.reference != reference
    ):
        raise NotFoundError("This confirmation is not available in this browser.")
    return receipt
