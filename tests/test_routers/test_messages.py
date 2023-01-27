from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.message import MessageSchema

from ..utils import days_ago


async def test_messages_list(client_superuser):
    since = days_ago(730).isoformat()
    until = days_ago(0).isoformat()
    response = await client_superuser.get(
        f"{configuration.base_url}/messages?since={since}&until={until}"
    )
    assert response.status_code == 200
    messages = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in messages}
    assert returned_ids == {1, 2, 3}


async def test_messages_list_errors(client_superuser):
    since = days_ago(730).isoformat()
    until = days_ago(0).isoformat()
    response = await client_superuser.get(
        f"{configuration.base_url}/messages?since={since}&until={until}&status=ERROR"
    )
    assert response.status_code == 200
    messages = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in messages}
    assert returned_ids == {2, 3}


async def test_messages_list_facility(client_superuser):
    since = days_ago(730).isoformat()
    until = days_ago(0).isoformat()
    response = await client_superuser.get(
        f"{configuration.base_url}/messages?since={since}&until={until}&facility=TEST_SENDING_FACILITY_2"
    )
    assert response.status_code == 200
    messages = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in messages}
    assert returned_ids == {3}


async def test_message_detail(client_superuser):
    response = await client_superuser.get(f"{configuration.base_url}/messages/1")
    assert response.status_code == 200
    print(response.json())
    error = MessageSchema(**response.json())
    assert error.id == 1


async def test_message_workitems(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/messages/2/workitems"
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


async def test_message_masterrecords(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/messages/1/masterrecords"
    )
    assert response.status_code == 200
    ids = {item.get("id") for item in response.json()}
    assert ids == {1}
