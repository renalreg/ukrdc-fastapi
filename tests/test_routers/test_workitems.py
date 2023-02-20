import pytest

from tests.utils import days_ago
from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.empi import WorkItemSchema
from ukrdc_fastapi.schemas.message import MessageSchema


async def test_workitems_list(client_authenticated):
    response = await client_authenticated.get(f"{configuration.base_url}/workitems")
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1, 3}


async def test_workitems_list_superuser(client_superuser):
    response = await client_superuser.get(f"{configuration.base_url}/workitems")
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1, 2, 3}


async def test_workitem_detail(client_authenticated):
    response = await client_authenticated.get(f"{configuration.base_url}/workitems/1")
    assert response.status_code == 200
    wi = WorkItemSchema(**response.json())
    assert wi.id == 1


async def test_workitem_detail_denied(client_authenticated):
    response = await client_authenticated.get(f"{configuration.base_url}/workitems/2")
    assert response.status_code == 403


async def test_workitem_related(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/workitems/1/related"
    )
    assert response.status_code == 200

    returned_ids = {item["id"] for item in response.json()}
    assert returned_ids == {3, 4}


async def test_workitem_related_superuser(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/workitems/1/related"
    )
    assert response.status_code == 200

    returned_ids = {item["id"] for item in response.json()}
    assert returned_ids == {2, 3, 4}


async def test_workitem_messages(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/workitems/1/messages"
    )
    assert response.status_code == 200

    errors = [MessageSchema(**item) for item in response.json()["items"]]
    message_ids = {error.id for error in errors}
    assert message_ids == {1, 2}


@pytest.mark.parametrize("workitem_id", [1, 2, 3])
async def test_workitem_close(client_superuser, workitem_id):
    response = await client_superuser.post(
        f"{configuration.base_url}/workitems/{workitem_id}/close", json={}
    )
    assert response.status_code == 200

    message = response.json().get("message")

    assert "<status>3</status>" in message
    assert f"<workitem>{workitem_id}</workitem>" in message
    assert "<updatedBy>TEST@UKRDC_FASTAPI</updatedBy>" in message


async def test_workitem_close_denied(client_authenticated):
    response = await client_authenticated.post(
        f"{configuration.base_url}/workitems/2/close", json={}
    )
    assert response.status_code == 403


async def test_workitem_update(client_superuser):
    response = await client_superuser.put(
        f"{configuration.base_url}/workitems/1",
        json={"status": 3, "comment": "UPDATE COMMENT"},
    )
    assert response.status_code == 200
    assert response.json().get("status") == "success"

    message = response.json().get("message")

    assert "<workitem>1</workitem>" in message
    assert "<status>3</status>" in message
    assert "<updateDescription>UPDATE COMMENT</updateDescription>" in message
    assert "<updatedBy>TEST@UKRDC_FASTAPI</updatedBy>" in message


async def test_workitem_update_denied(client_authenticated):
    response = await client_authenticated.put(
        f"{configuration.base_url}/workitems/2",
        json={"status": 3, "comment": "UPDATE COMMENT"},
    )
    assert response.status_code == 403
