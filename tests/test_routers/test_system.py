import pytest

from ukrdc_fastapi.dependencies.auth import Permissions
from ukrdc_fastapi.config import configuration


def test_user(client):
    response = client.get(f"{configuration.base_url}/v1/system/user/")
    assert response.json().get("email") == "TEST@UKRDC_FASTAPI"
    assert set(response.json().get("permissions")) == set(Permissions.all())


def test_info(client):
    response = client.get(f"{configuration.base_url}/v1/system/info/")
    assert response.json() == {
        "githubSha": None,
        "githubRef": None,
        "deploymentEnv": "development",
    }
