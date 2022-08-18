import json
from typing import Any, Optional, Type

from redis import Redis
from starlette.requests import Request
from starlette.responses import Response

from ukrdc_fastapi.utils.encoder import JsonEncoder


class CacheNotSetException(Exception):
    pass


class BasicCache:
    # Create a sentinel object so we can tell the difference between no cached value,
    # and a cached None value
    _sentinel = object()

    def __init__(
        self,
        redis: Redis,
        key: str,
        encoder: Type[json.JSONEncoder] = JsonEncoder,
        prefix: str = "response-cache:",
    ) -> None:
        self.redis = redis
        self.encoder: Type[json.JSONEncoder] = encoder
        self.prefix = prefix

        self.key: str = key

        # Enable pre-retreiving cached value on init
        self._cached_value_str: Optional[str] = None
        self._cached_value: Optional[Any] = BasicCache._sentinel

        # Pre-fetch the cached value
        if self.redis.exists(self.key):
            # Get the value string from Redis
            value_str = self.redis.get(self.key)
            # Store the cached value string
            self._cached_value_str = value_str
            # Convert to JSON if the value is not None, then store the value in self._cached_value
            self._cached_value = (
                json.loads(value_str) if value_str is not None else None
            )

    @property
    def exists(self) -> bool:
        """Check if a cached value for this key exists

        Returns:
            bool: Does the cached value exist
        """
        return self._cached_value is not BasicCache._sentinel

    def get(self) -> Any:
        """Get the current cached value for this key

        Raises:
            CacheNotSetException: Cached value is missing or expired, and no new value has been set.

        Returns:
            Any: Cached value
        """
        if self._cached_value is BasicCache._sentinel:
            raise CacheNotSetException(
                f"No value for key {self.key} was found in the cache. Set a value by calling cache.set(obj)."
            )

        return self._cached_value

    def _dump_to_memory(self, obj: Any) -> None:
        # Create a string representation of the object
        value_str = json.dumps(obj, cls=self.encoder)
        # Hold the cached value string in memory for the duration of this request
        self._cached_value_str = value_str
        # Hold the cached value in memory for the duration of this request
        self._cached_value = json.loads(value_str)

    def set(self, obj: Any, expire: Optional[int] = None) -> None:
        """Set a new cached value for this key

        Args:
            obj (Any): New value to cache
            expire (Optional[int]): Expiry time in seconds. Defaults to None.
        """
        # Dump the object to a string, and store in the cache class instance
        self._dump_to_memory(obj)

        # Set the value in Redis
        if self._cached_value_str:
            self.redis.set(self.key, self._cached_value_str, ex=expire)


class ResponseCache(BasicCache):
    def __init__(
        self,
        redis: Redis,
        key: str,
        request: Request,
        response: Response,
        encoder: Type[json.JSONEncoder] = JsonEncoder,
        prefix: str = "response-cache:",
    ) -> None:
        super().__init__(redis, key, encoder, prefix)

        # If we have a cached value string already set, set the etag header
        if self._cached_value_str is not None:
            self._set_etag(self._cached_value_str)

        self.request: Request = request
        self.response: Response = response

    @property
    def no_store(self) -> bool:
        """Check if the incoming request has a 'Cache-Control: no-store' header

        Returns:
            bool: Does the incoming request have a 'Cache-Control: no-store' header
        """
        if self.request.headers.get("Cache-Control") == "no-store":
            return True
        return False

    def _set_etag(self, value_str: Optional[str]):
        """Set the etag header for a given resource string

        Args:
            value_str (Optional[str]): Value to hash for the etag header
        """
        self.etag = f"W/{hash(value_str)}"

    def set(self, obj: Any, expire: Optional[int] = None) -> None:
        """Set a new cached value for this key

        Args:
            obj (Any): New value to cache
            expire (Optional[int]): Expiry time in seconds. Defaults to None.
        """
        # Dump the object to a string, and store in the cache class instance
        self._dump_to_memory(obj)

        # Set the value in Redis
        if self._cached_value_str:
            # Set the etag
            self._set_etag(self._cached_value_str)

            # If the client hasn't forbidden caching for this request
            if not self.no_store:
                # Set the value in Redis
                self.redis.set(self.key, self._cached_value_str, ex=expire)

    def prepare_response(self):
        """Add cache related headers to the response object"""
        ttl = self.redis.ttl(self.key)
        if ttl:
            self.response.headers["Cache-Control"] = f"max-age={ttl}"
        if self.etag:
            self.response.headers["ETag"] = self.etag
