import logging

from fastapi_utils.tasks import repeat_every
from ukrdc_sqla.ukrdc import Code

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_redis
from ukrdc_fastapi.dependencies.database import (
    ErrorsSession,
    JtraceSession,
    Ukrdc3Session,
)
from ukrdc_fastapi.query.dashboard import get_empi_stats, get_workitems_stats
from ukrdc_fastapi.query.facilities import _get_and_cache_facility


@repeat_every(seconds=settings.cache_statistics_seconds)
def cache_all_facilities() -> None:
    ukrdc3 = Ukrdc3Session()
    errorsdb = ErrorsSession()
    redis = get_redis()
    logging.info("Refreshing facility statistics")
    codes = ukrdc3.query(Code).filter(Code.coding_standard == "RR1+").all()
    for code in codes:
        logging.debug(f"Caching {code.code}")
        _get_and_cache_facility(code, ukrdc3, errorsdb, redis)


@repeat_every(seconds=settings.cache_dashboard_seconds)
def cache_dash_stats() -> None:
    jtrace = JtraceSession()
    redis = get_redis()
    logging.info("Refreshing admin statistics")
    get_workitems_stats(jtrace, redis, refresh=True)
    get_empi_stats(jtrace, redis, refresh=True)
