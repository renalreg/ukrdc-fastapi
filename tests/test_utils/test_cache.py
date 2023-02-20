import pytest
from pydantic import BaseModel

from ukrdc_fastapi.utils.cache import (
    BasicCache,
    CacheNotSetException,
    DynamicCacheKey,
    TestCachePrefix,
)


class PydanticSubModel(BaseModel):
    inner_string: str
    inner_int: int


class PydanticModel(BaseModel):
    string: str
    int: int
    float: float
    bool: bool
    sub_model: PydanticSubModel


def test_basic_cache_empty(redis_session):
    cache = BasicCache(redis_session, DynamicCacheKey(TestCachePrefix.PYTEST, "1"))
    assert cache.exists is False

    with pytest.raises(CacheNotSetException):
        cache.get()


def test_basic_cache_set_primitive(redis_session):
    cache = BasicCache(redis_session, DynamicCacheKey(TestCachePrefix.PYTEST, "2"))
    assert cache.exists is False

    cache.set("foo")

    assert cache.exists is True

    assert cache.get() == "foo"


def test_basic_cache_set_dict(redis_session):
    cache = BasicCache(redis_session, DynamicCacheKey(TestCachePrefix.PYTEST, "3"))
    assert cache.exists is False

    cache.set(
        {
            "string": "foo",
            "int": 1,
            "float": 1.0,
            "bool": True,
            "dict": {"foo": "bar"},
        }
    )

    assert cache.exists is True

    assert cache.get() == {
        "string": "foo",
        "int": 1,
        "float": 1.0,
        "bool": True,
        "dict": {"foo": "bar"},
    }


def test_basic_cache_set_pydantic(redis_session):
    cache = BasicCache(redis_session, DynamicCacheKey(TestCachePrefix.PYTEST, "4"))
    assert cache.exists is False

    cache.set(
        PydanticModel(
            string="foo",
            int=1,
            float=1.0,
            bool=True,
            sub_model=PydanticSubModel(inner_string="bar", inner_int=2),
        )
    )

    assert cache.exists is True

    assert cache.get() == {
        "string": "foo",
        "int": 1,
        "float": 1.0,
        "bool": True,
        "sub_model": {
            "inner_string": "bar",
            "inner_int": 2,
        },
    }


def test_basic_cache_restore(redis_session):
    cache_key = DynamicCacheKey(TestCachePrefix.PYTEST, "5")

    cache_1 = BasicCache(redis_session, cache_key)
    assert cache_1.exists is False
    cache_1.set("foo")

    # Create a new cache object (no value stored in memory)
    cache_2 = BasicCache(redis_session, cache_key)

    # Redis value should match in-memory value
    assert cache_1.get() == cache_2.get()
