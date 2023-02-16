from ukrdc_fastapi.config import configuration


async def test_merge(client_superuser):
    response = await client_superuser.post(
        f"{configuration.base_url}/empi/merge",
        json={"superseding": 1, "superseded": 2},
    )
    assert response.status_code == 200
    assert response.json().get("status") == "success"


async def test_merge_denied(client_authenticated):
    response = await client_authenticated.post(
        f"{configuration.base_url}/empi/merge",
        json={"superseding": 1, "superseded": 3},
    )
    assert response.status_code == 403

    response = await client_authenticated.post(
        f"{configuration.base_url}/empi/merge",
        json={"superseding": 3, "superseded": 1},
    )
    assert response.status_code == 403


async def test_unlink(client_superuser):
    response = await client_superuser.post(
        f"{configuration.base_url}/empi/unlink",
        json={"personId": 4, "comment": "comment", "masterId": 1},
    )

    assert response.json().get("id") == 4


async def test_unlink_denied(client_authenticated):
    response = await client_authenticated.post(
        f"{configuration.base_url}/empi/unlink",
        json={"personId": 3, "comment": "comment", "masterId": 3},
    )
    assert response.status_code == 403
