"""Aggregates every v1 router behind a single prefix."""

from fastapi import APIRouter

from app.api.v1.routers import auth, bookings, contact, gallery, inquiries, portfolios

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(portfolios.router)
api_router.include_router(gallery.router)
api_router.include_router(inquiries.router)
api_router.include_router(bookings.router)
api_router.include_router(contact.router)

__all__ = ["api_router"]
