from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.message import MessageSchema

from ..utils import days_ago

SINCE = days_ago(730).isoformat()
UNTIL = days_ago(0).isoformat()


async def test_messages_list(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/messages?since={SINCE}&until={UNTIL}"
    )
    assert response.status_code == 200
    messages = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in messages}
    assert returned_ids == {1, 2}


async def test_messages_list_superuser(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/messages?since={SINCE}&until={UNTIL}"
    )
    assert response.status_code == 200
    messages = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in messages}
    assert returned_ids == {1, 2, 3}


async def test_message_detail(client_authenticated):
    response = await client_authenticated.get(f"{configuration.base_url}/messages/1")
    assert response.status_code == 200


async def test_message_detail_denied(client_authenticated):
    response = await client_authenticated.get(f"{configuration.base_url}/messages/3")
    assert response.status_code == 403


async def test_message_workitems(client_authenticated, client_superuser):
    response = await client_authenticated.get(
        f"{configuration.base_url}/messages/1/workitems"
    )
    assert response.status_code == 200
    ids = {item.get("id") for item in response.json()}
    assert ids == set()

    response = await client_superuser.get(
        f"{configuration.base_url}/messages/3/workitems"
    )
    assert response.status_code == 200
    ids = {item.get("id") for item in response.json()}
    assert ids == {3}


async def test_message_workitems_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/messages/3/workitems"
    )
    assert response.status_code == 403


async def test_message_masterrecords(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/messages/1/masterrecords"
    )
    assert response.status_code == 200
    ids = {item.get("id") for item in response.json()}
    assert ids == {1}


async def test_message_masterrecords_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/messages/3/masterrecords"
    )
    assert response.status_code == 403
