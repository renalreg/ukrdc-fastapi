import pytest

from tests.utils import days_ago
from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.empi import WorkItemSchema
from ukrdc_fastapi.schemas.message import MessageSchema


async def test_workitems_list(client_superuser):
    response = await client_superuser.get(f"{configuration.base_url}/workitems")
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1, 2, 3}


async def test_workitems_list_filter_since(client_superuser):
    since = days_ago(2).isoformat()
    response = await client_superuser.get(
        f"{configuration.base_url}/workitems?since={since}"
    )
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {2, 3}


async def test_workitems_list_filter_until(client_superuser):
    until = days_ago(365).isoformat()
    response = await client_superuser.get(
        f"{configuration.base_url}/workitems?until={until}"
    )
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1}


async def test_workitem_detail(client_superuser):
    response = await client_superuser.get(f"{configuration.base_url}/workitems/1")
    assert response.status_code == 200
    wi = WorkItemSchema(**response.json())
    assert wi.id == 1


async def test_workitem_related(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/workitems/1/related"
    )
    assert response.status_code == 200

    returned_ids = {item["id"] for item in response.json()}
    assert returned_ids == {2, 3, 4}


async def test_workitem_messages(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/workitems/1/messages"
    )
    assert response.status_code == 200

    errors = [MessageSchema(**item) for item in response.json()["items"]]
    message_ids = {error.id for error in errors}
    assert message_ids == {1, 2}


async def test_workitem_errors(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/workitems/1/messages?status=ERROR"
    )
    assert response.status_code == 200

    errors = [MessageSchema(**item) for item in response.json()["items"]]
    message_ids = {error.id for error in errors}
    assert message_ids == {2}


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
