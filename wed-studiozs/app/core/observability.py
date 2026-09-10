"""JSON logging and low-cardinality ASGI request instrumentation."""

from __future__ import annotations

import json
import logging
import re
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime

from prometheus_client import CollectorRegistry, Counter, Histogram
from sqlalchemy.engine import make_url
from starlette.datastructures import MutableHeaders
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Message, Receive, Scope, Send

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)
route_context: ContextVar[str | None] = ContextVar("route", default=None)
_SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE", "CONNECT"})


class JsonFormatter(logging.Formatter):
    def __init__(self, secrets: tuple[str, ...] = ()) -> None:
        super().__init__()
        self.secrets = tuple(value for value in secrets if value)

    def format(self, record: logging.LogRecord) -> str:
        # Uvicorn's normal access message contains the raw URL/query string.
        message = "HTTP request" if record.name == "uvicorn.access" else record.getMessage()
        for secret in self.secrets:
            message = message.replace(secret, "[REDACTED]")
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "request_id": request_id_context.get(),
        }
        if record.name == "uvicorn.access":
            payload["route"] = route_context.get() or "unmatched"
            if isinstance(record.args, tuple) and len(record.args) == 5:
                method, status = record.args[1], record.args[4]
                payload["method"] = method if method in _METHODS else "OTHER"
                payload["status"] = status
        for key in ("route", "method", "status", "duration_seconds"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            # Exception text and locals can contain SQL parameters and credentials.
            payload["exception_type"] = record.exc_info[0].__name__
        for key, value in payload.items():
            if isinstance(value, str):
                for secret in self.secrets:
                    value = value.replace(secret, "[REDACTED]")
                payload[key] = value
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(*, debug: bool, secret_key: str, database_url: str) -> None:
    password = make_url(database_url).password or ""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter((secret_key, database_url, password)))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
        logger.disabled = False
        logger.setLevel(logging.INFO)
    for name, logger in logging.Logger.manager.loggerDict.items():
        if name.startswith("sqlalchemy.") and isinstance(logger, logging.Logger):
            logger.handlers.clear()
            logger.propagate = True
    for name in ("sqlalchemy.engine", "aiosqlite", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)


class RequestMetrics:
    def __init__(self) -> None:
        # Each factory-created app owns its registry, avoiding global duplicates.
        self.registry = CollectorRegistry()
        labels = ("route", "method", "status")
        self.requests = Counter(
            "wed_http_requests_total", "Completed HTTP requests.", labels, registry=self.registry
        )
        self.duration = Histogram(
            "wed_http_request_duration_seconds",
            "HTTP request duration including response streaming.",
            labels,
            registry=self.registry,
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
        )


def _route(scope: Scope) -> str:
    if isinstance(scope.get("endpoint"), StaticFiles):
        return "/static/{path:path}"
    route = scope.get("route")
    return getattr(route, "path", None) or "unmatched"


class ObservabilityMiddleware:
    """Wrap the error middleware too, so unhandled 500s get headers and metrics."""

    def __init__(self, app: ASGIApp, metrics: RequestMetrics) -> None:
        self.app = app
        self.metrics = metrics

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        supplied = [value for key, value in scope.get("headers", []) if key.lower() == b"x-request-id"]
        candidate = supplied[0].decode("latin-1") if len(supplied) == 1 else ""
        request_id = candidate if _SAFE_REQUEST_ID.fullmatch(candidate) else uuid.uuid4().hex
        token = request_id_context.set(request_id)
        route_token = route_context.set(None)
        scope.setdefault("state", {})["request_id"] = request_id
        method = scope["method"] if scope["method"] in _METHODS else "OTHER"
        started = time.perf_counter()
        status = 500

        async def send_with_request_id(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                route_context.set(_route(scope))
                MutableHeaders(scope=message)["X-Request-ID"] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            duration = time.perf_counter() - started
            route = _route(scope)
            labels = (route, method, str(status))
            self.metrics.requests.labels(*labels).inc()
            self.metrics.duration.labels(*labels).observe(duration)
            logging.getLogger("wed_studiozs.request").info(
                "HTTP request completed",
                extra={"route": route, "method": method, "status": status, "duration_seconds": duration},
            )
            route_context.reset(route_token)
            request_id_context.reset(token)
