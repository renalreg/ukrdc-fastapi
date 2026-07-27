"""
Structured logging for the UKRDC FastAPI app.

Mirrors the shape of the webapi Django `LOGGING` setting (formatters / handlers
/ loggers), but adds a "request" formatter driven by RequestLoggingMiddleware
so logs look like:

    2026-07-27 16:43:05 INFO client=192.168.234.45 request="GET /api/facilities HTTP/1.1" status=200 duration_ms=12.4

instead of uvicorn's default:

    INFO:     192.168.234.45:0 - "GET /api/facilities HTTP/1.0" 200 OK
"""

import logging
import logging.config
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ukrdc_fastapi.config import settings

APP_LOG_LEVEL = "DEBUG" if settings.debug else settings.log_level
ACCESS_LOG_LEVEL = settings.access_log_level

access_logger = logging.getLogger("ukrdc_fastapi.access")


class SafeRequestFormatter(logging.Formatter):
    """
    Formatter used by the "request" handler. Falls back to "-" for any of
    the custom fields (client_ip, method, path, etc) if a record was logged
    without them, so a stray log call on the access logger can't KeyError.
    """

    DEFAULTS = {
        "client_ip": "-",
        "method": "-",
        "path": "-",
        "http_version": "-",
        "status_code": "-",
        "duration_ms": "-",
    }

    def format(self, record: logging.LogRecord) -> str:
        for key, default in self.DEFAULTS.items():
            if not hasattr(record, key):
                setattr(record, key, default)
        return super().format(record)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(module)s P%(process)d T%(thread)d %(message)s",
        },
        "standard": {
            "format": "%(asctime)s [%(module)s(%(funcName)s:%(lineno)s)] %(levelname)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "request": {
            "()": "ukrdc_fastapi.dependencies.logging.SafeRequestFormatter",
            "format": (
                "%(asctime)s %(levelname)s "
                "client=%(client_ip)s "
                'request="%(method)s %(path)s HTTP/%(http_version)s" '
                "status=%(status_code)s "
                "duration_ms=%(duration_ms)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": APP_LOG_LEVEL,
            "formatter": "standard",
        },
        "console_access": {
            "class": "logging.StreamHandler",
            "level": ACCESS_LOG_LEVEL,
            "formatter": "request",
        },
    },
    "loggers": {
        # Your own application code: logging.getLogger("ukrdc_fastapi.something")
        "ukrdc_fastapi": {
            "handlers": ["console"],
            "level": APP_LOG_LEVEL,
            "propagate": False,
        },
        # Structured access log, fed by RequestLoggingMiddleware
        "ukrdc_fastapi.access": {
            "handlers": ["console_access"],
            "level": ACCESS_LOG_LEVEL,
            "propagate": False,
        },
        # Keep uvicorn's error/startup logs, but drop its own access logger
        # so requests aren't logged twice.
        "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": [], "level": "CRITICAL", "propagate": False},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
}


def configure_logging() -> None:
    """Apply the LOGGING dict. Call this once, before the app is created."""
    logging.config.dictConfig(LOGGING)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request through `ukrdc_fastapi.access` with timing info."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()

        # Handles being behind a reverse proxy (nginx, ALB, etc.)
        client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else "-"

        status_code = 500  # assume worst case until we know otherwise
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            access_logger.info(
                "",
                extra={
                    "client_ip": client_ip,
                    "method": request.method,
                    "path": request.url.path
                    + (f"?{request.url.query}" if request.url.query else ""),
                    "http_version": request.scope.get("http_version", "-"),
                    "status_code": status_code,
                    "duration_ms": f"{duration_ms:.1f}",
                },
            )
