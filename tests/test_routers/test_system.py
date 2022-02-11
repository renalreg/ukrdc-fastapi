import pytest

from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.dependencies.auth import Permissions


async def test_user(client):
    response = await client.get(f"{configuration.base_url}/v1/system/user/")
    assert response.json().get("email") == "TEST@UKRDC_FASTAPI"
    assert set(response.json().get("permissions")) == set(Permissions.all())


async def test_info(client):
    response = await client.get(f"{configuration.base_url}/v1/system/info/")
    assert response.json() == {
        "githubSha": None,
        "githubRef": None,
        "deploymentEnv": "development",
    }
