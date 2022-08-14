from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.dependencies.auth import Permissions
from ukrdc_fastapi.schemas.user import UserPreferences


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
        "version": configuration.version,
    }


async def test_read_system_user_preferences(client):
    response = await client.get(f"{configuration.base_url}/v1/system/user/preferences/")
    # In the absence of any manually-set preferences, ensure we get default values back
    assert UserPreferences(**response.json()) == UserPreferences().dict()


async def test_update_system_user_preferences_show_ukrdc(client):
    response = await client.put(
        f"{configuration.base_url}/v1/system/user/preferences/",
        json={"searchShowUkrdc": True},
    )
    # Ensure we get the new value back
    assert UserPreferences(**response.json()).search_show_ukrdc == True
