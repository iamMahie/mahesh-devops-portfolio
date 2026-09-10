"""FastAPI application factory and entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.types import ASGIApp

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.lifecycle import DatabaseNotReady, check_database
from app.core.observability import ObservabilityMiddleware, RequestMetrics, configure_logging
from app.db.session import engine
from app.web.router import router as web_router
from app.web.templates import STATIC_DIR

configure_logging(
    debug=settings.debug, secret_key=settings.secret_key, database_url=settings.database_url
)
logger = logging.getLogger("wed_studiozs")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Refuse traffic before migration; release the pool even on startup failure."""
    try:
        try:
            await check_database(app.state.db_engine, settings.schema_check_timeout_seconds)
        except DatabaseNotReady as exc:
            logger.error("Startup refused: %s", exc)
            raise
        logger.info("Database schema compatibility verified.")
        yield
    finally:
        await app.state.db_engine.dispose()
        logger.info("Database engine disposed.")


class InstrumentedFastAPI(FastAPI):
    def build_middleware_stack(self) -> ASGIApp:
        return ObservabilityMiddleware(super().build_middleware_stack(), self.state.metrics)


def create_app() -> FastAPI:
    app = InstrumentedFastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Wedding & event photography platform - portfolios, inquiries and bookings.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.state.db_engine = engine
    app.state.metrics = RequestMetrics()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    app.include_router(web_router)

    @app.get("/healthz", tags=["system"], summary="Liveness probe")
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    @app.get("/readyz", tags=["system"], summary="Readiness probe")
    async def readyz(response: Response) -> dict[str, str]:
        try:
            await check_database(app.state.db_engine, settings.schema_check_timeout_seconds)
        except DatabaseNotReady:
            logger.warning("Readiness check failed.")
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": "unavailable"}
        return {"status": "ready"}

    @app.get("/metrics", tags=["system"], include_in_schema=False)
    async def metrics() -> Response:
        return Response(
            content=generate_latest(app.state.metrics.registry),
            headers={"Content-Type": CONTENT_TYPE_LATEST},
        )

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=settings.debug)
