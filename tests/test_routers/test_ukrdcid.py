from ukrdc_fastapi.config import configuration


async def test_record_membership_pkb_superuser(client_superuser):
    response = await client_superuser.post(
        f"{configuration.base_url}/ukrdcid/999999999/memberships/create/pkb",
    )
    assert response.status_code == 200


async def test_record_membership_pkb(client_authenticated):
    response = await client_authenticated.post(
        f"{configuration.base_url}/ukrdcid/999999911/memberships/create/pkb",
    )

    assert response.status_code == 403


async def test_record_membership_mrc_superuser(client_superuser):
    response = await client_superuser.post(
        f"{configuration.base_url}/ukrdcid/999999999/memberships/create/mrc",
    )
    assert response.status_code == 200


async def test_record_membership_mrc(client_authenticated):
    response = await client_authenticated.post(
        f"{configuration.base_url}/ukrdcid/999999911/memberships/create/mrc",
    )

    assert response.status_code == 403
