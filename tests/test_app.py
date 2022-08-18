import pytest

from ukrdc_fastapi.main import app


class TrailingSlashException(Exception):
    pass


@pytest.mark.parametrize("route", app.routes)
def test_route_url_format(route):
    if route.path[-1] == "/":
        raise TrailingSlashException(f"Route {route.path} has a trailing slash")
