from fastapi import Depends
from redis import Redis
from starlette.requests import Request
from starlette.responses import Response

from ukrdc_fastapi.dependencies import get_redis
from ukrdc_fastapi.utils.cache import (
    CacheKey,
    DynamicCacheKey,
    FacilityCachePrefix,
    ResponseCache,
)


def cache_factory(cachekey: CacheKey):
    """
    Build a cache dependency function. The returned function
    can be used as a FastAPI dependency.

    Args:
        key (CacheKey): Key describing the cached data
    """

    def cache_factory_dependency(
        request: Request,
        response: Response,
        redis: Redis = Depends(get_redis),
    ) -> ResponseCache:
        """
        FastAPI dependency to create a cache object.
        Arguments are automatically populated by the FastAPI dependency system.

        Args:
            request (Request): Request object
            response (Response): Response object
            redis (Redis): Redis cache session

        Returns:
            ResponseCache: ResponseCache instance with pre-populated key
        """
        return ResponseCache(redis, cachekey, request, response)

    return cache_factory_dependency


def facility_cache_factory(prefix: FacilityCachePrefix):
    """
    Build a facility cache dependency function. The returned function
    can be used as a FastAPI dependency, and will generate a cache key
    based on the prefix and facility code in the URL path.

    Args:
        prefix (FacilityCachePrefix): Key prefix enum attribute describing the cached data
    """

    def facility_cache_factory_dependency(
        code: str,
        request: Request,
        response: Response,
        redis: Redis = Depends(get_redis),
    ) -> ResponseCache:
        """
        FastAPI dependency to create a cache object for facility data.
        Reads the facility code to generate a cache key.
        Arguments are automatically populated by the FastAPI dependency system.

        Args:
            code (str): Facility code (read from the URL path)
            request (Request): Request object
            response (Response): Response object
            redis (Redis): Redis cache session

        Returns:
            ResponseCache: ResponseCache instance with pre-populated key
        """
        cachekey = DynamicCacheKey(prefix, code)
        return ResponseCache(redis, cachekey, request, response)

    return facility_cache_factory_dependency
