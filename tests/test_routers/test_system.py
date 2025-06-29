from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.dependencies.auth import Permissions
from ukrdc_fastapi.schemas.user import UserPreferences


async def test_user_info(client_superuser):
    response = await client_superuser.get(f"{configuration.base_url}/system/user")
    assert response.json().get("email") == "TEST@UKRDC_FASTAPI"
    assert set(response.json().get("permissions")) == set(Permissions.all())


async def test_info(client_superuser):
    response = await client_superuser.get(f"{configuration.base_url}/system/info")
    assert response.json() in [
        {
            "githubSha": "",
            "githubRef": "",
            "deploymentEnv": "development",
            "version": configuration.version,
        },
        {
            "githubSha": None,
            "githubRef": None,
            "deploymentEnv": "development",
            "version": configuration.version,
        },
    ]


async def test_read_system_user_preferences(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/system/user/preferences"
    )
    # In the absence of any manually-set preferences, ensure we get default values back
    assert UserPreferences(**response.json()) == UserPreferences().dict()


async def test_update_system_user_preferences_placeholder(client_superuser):
    response = await client_superuser.put(
        f"{configuration.base_url}/system/user/preferences",
        json={"placeholder": True},
    )
    # Ensure we get the new value back
    assert UserPreferences(**response.json()).placeholder is True
