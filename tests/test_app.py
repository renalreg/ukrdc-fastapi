import pytest

from ukrdc_fastapi.main import app


class TrailingSlashException(Exception):
    pass


@pytest.mark.parametrize("path", app.openapi()["paths"].keys())
def test_route_url_format(path):
    if path[-1] == "/":
        raise TrailingSlashException(f"Route {path} has a trailing slash")
