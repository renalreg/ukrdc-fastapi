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
import warnings
from typing import ClassVar

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from ukrdc_stats.exceptions import EmptyCohortError, NoCohortError, NoTestsError

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

    DEFAULTS: ClassVar[dict[str, str]] = {
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
        "ukrdc_stats": {  # TODO revist once the ukrdc-stats issues have been fixed
            "handlers": ["console"],
            "level": "CRITICAL",
            "propagate": False,
        },
        "py.warnings": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
}


def configure_logging() -> None:
    """Apply the LOGGING dict. Call this once, before the app is created."""
    # ukrdc_stats occasionally calls numpy's nanmean on an empty group (e.g. a
    # facility/stat with no matching data), which is expected and not
    # actionable - suppress it at the source rather than logging it.
    warnings.filterwarnings(
        "ignore",
        message="Mean of empty slice",
        category=RuntimeWarning,
        module="numpy",
    )
    # Route any other warnings.warn() calls into the logging system so they're
    # subject to the same level filtering/formatting as everything else.
    logging.captureWarnings(True)

    logging.config.dictConfig(LOGGING)


def _raise_site(exc: BaseException) -> tuple[str, int, str]:
    """
    Walk to the innermost frame of exc's traceback - i.e. where it was
    actually raised, not wherever we're currently catching it - and return
    (pathname, lineno, func_name) for that frame. Tracebacks grow a new
    frame at the front each time an exception propagates up a call stack,
    so the *last* tb_next is the original raise site.
    """
    tb = exc.__traceback__
    if tb is None:
        return (__file__, 0, "unknown")
    while tb.tb_next is not None:
        tb = tb.tb_next
    frame = tb.tb_frame
    return (frame.f_code.co_filename, tb.tb_lineno, frame.f_code.co_name)


async def _ukrdc_stats_error_handler(_, exc):
    """
    Handles NoCohortError/EmptyCohortError/NoTestsError raised by ukrdc_stats
    when a facility has no feed, an empty cohort, or no test results to
    compute stats from. Logged at ERROR and attributed to where ukrdc_stats
    actually raised it (not this handler), so the log line still points at
    the real source without a full traceback.
    """
    logger = logging.getLogger("ukrdc_fastapi")
    if logger.isEnabledFor(logging.ERROR):
        pathname, lineno, func_name = _raise_site(exc)
        record = logger.makeRecord(
            logger.name,
            logging.ERROR,
            pathname,
            lineno,
            "ukrdc_stats error: %s",
            (exc,),
            None,
            func=func_name,
        )
        logger.handle(record)
    return PlainTextResponse(str(exc), status_code=404)


def register_ukrdc_stats_exception_handlers(app: FastAPI) -> None:
    """Register ukrdc_stats data-availability exceptions as 404s instead of 500s."""
    for exc_class in (NoCohortError, EmptyCohortError, NoTestsError):
        app.add_exception_handler(exc_class, _ukrdc_stats_error_handler)


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
