import json
from typing import Any, Optional, Tuple, Type

from fastapi import APIRouter, Depends, Security
from redis import Redis
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response

from ukrdc_fastapi.dependencies import get_redis, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.facilities.stats.demographics import (
    FacilityDemographicStats,
    get_facility_stats_demographics,
)
from ukrdc_fastapi.utils.encoder import JsonEncoder

router = APIRouter(tags=["Facilities/Stats"], prefix="/{code}/stats")


class CacheNotInitialisedException(Exception):
    pass


class ResponseCache:
    def __init__(
        self,
        redis: Redis,
        encoder: Type[json.JSONEncoder] = JsonEncoder,
        prefix: str = "response-cache:",
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ) -> None:
        self.redis = redis
        self.encoder: Type[json.JSONEncoder] = encoder
        self.prefix = prefix

        # TODO: Check for no-cache header
        self.request: Optional[Request] = request
        self.response: Optional[Response] = response

        self.key: Optional[str] = None

    def init(self, key: str) -> None:
        self.key = f"{self.prefix}{key}"

    def set(self, obj, expire: Optional[int] = None) -> None:
        if not self.key:
            raise CacheNotInitialisedException("Cache must be initialised before use.")

        value_str = json.dumps(obj, cls=self.encoder)
        self.redis.set(self.key, value_str, ex=expire)

    def get(self) -> Any:
        if not self.key:
            raise CacheNotInitialisedException("Cache must be initialised before use.")

        value_str = self.redis.get(self.key)
        if value_str is not None:
            return json.loads(value_str)
        return None

    def get_with_etag(self) -> Tuple[Any, int]:
        if not self.key:
            raise CacheNotInitialisedException("Cache must be initialised before use.")

        value_str = self.redis.get(self.key)
        if value_str is not None:
            return json.loads(value_str), hash(value_str)

        return None, hash(None)

    def exists(self) -> bool:
        if not self.key:
            raise CacheNotInitialisedException("Cache must be initialised before use.")
        return bool(self.redis.exists(self.key))

    def respond(self) -> Any:
        if not self.key:
            raise CacheNotInitialisedException("Cache must be initialised before use.")
        ttl = self.redis.ttl(self.key)
        val, etag = self.get_with_etag()
        if self.response:
            if ttl:
                self.response.headers["Cache-Control"] = f"max-age={ttl}"
            if val:
                self.response.headers["ETag"] = f"W/{etag}"
        return val


def get_cache(request: Request, response: Response, redis: Redis = Depends(get_redis)):
    return ResponseCache(redis, request=request, response=response)


@router.get("/demographics", response_model=FacilityDemographicStats)
def facility_stats_demographics(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    user: UKRDCUser = Security(auth.get_user()),
    cache: ResponseCache = Depends(get_cache),
):
    """Retreive demographic distributions for a given facility"""
    # Set our cache key
    cache.init(f"facilities:demographics:{code}")

    if not cache.exists():
        # Cache a computed value, and expire after 8 hours
        cache.set(get_facility_stats_demographics(ukrdc3, code, user), expire=28800)

    # Generate a response including cache information in the response headers
    return cache.respond()
