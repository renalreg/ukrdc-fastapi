import pytest

from ukrdc_fastapi.routers.api.v1 import system


def test_user(client):
    response = client.get("/api/v1/system/user/")
    assert response.json().get("email") == "TEST@UKRDC_FASTAPI"
    assert set(response.json().get("permissions")) == set(
        [
            "ukrdc:records:read",
            "ukrdc:messages:read",
            "ukrdc:mirth:read",
            "ukrdc:workitems:read",
            "ukrdc:codes:read",
            "ukrdc:records:write",
            "ukrdc:messages:write",
            "ukrdc:mirth:write",
            "ukrdc:workitems:write",
            "ukrdc:codes:write",
            "ukrdc:records:export",
            "ukrdc:records:delete",
            "ukrdc:empi:write",
            "ukrdc:unit:*",
        ]
    )


def test_info(client):
    response = client.get("/api/v1/system/info/")
    assert response.json() == {
        "githubSha": "Not Available",
        "githubRef": "Not Available",
        "deploymentEnv": "development",
    }
