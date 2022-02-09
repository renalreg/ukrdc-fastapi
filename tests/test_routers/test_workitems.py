import pytest

from tests.utils import days_ago
from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.empi import WorkItemSchema
from ukrdc_fastapi.schemas.message import MessageSchema


async def test_workitems_list(client):
    response = await client.get(f"{configuration.base_url}/v1/workitems")
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1, 2, 3}


async def test_workitems_list_filter_since(client):
    since = days_ago(2).isoformat()
    response = await client.get(f"{configuration.base_url}/v1/workitems?since={since}")
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {2, 3}


async def test_workitems_list_filter_until(client):
    until = days_ago(365).isoformat()
    response = await client.get(f"{configuration.base_url}/v1/workitems?until={until}")
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1}


async def test_workitem_detail(client):
    response = await client.get(f"{configuration.base_url}/v1/workitems/1")
    assert response.status_code == 200
    wi = WorkItemSchema(**response.json())
    assert wi.id == 1


async def test_workitem_related(client):
    response = await client.get(f"{configuration.base_url}/v1/workitems/1/related")
    assert response.status_code == 200

    returned_ids = {item["id"] for item in response.json()}
    assert returned_ids == {2, 3, 4}


async def test_workitem_messages(client):
    response = await client.get(f"{configuration.base_url}/v1/workitems/1/messages")
    assert response.status_code == 200

    errors = [MessageSchema(**item) for item in response.json()["items"]]
    message_ids = {error.id for error in errors}
    assert message_ids == {1, 3}


async def test_workitem_errors(client):
    response = await client.get(
        f"{configuration.base_url}/v1/workitems/1/messages/?status=ERROR"
    )
    assert response.status_code == 200

    errors = [MessageSchema(**item) for item in response.json()["items"]]
    message_ids = {error.id for error in errors}
    assert message_ids == {1}


@pytest.mark.parametrize("workitem_id", [1, 2, 3])
async def test_workitem_close(client, workitem_id):
    response = await client.post(
        f"{configuration.base_url}/v1/workitems/{workitem_id}/close/", json={}
    )
    assert response.status_code == 200

    message = response.json().get("message")

    assert "<status>3</status>" in message
    assert f"<workitem>{workitem_id}</workitem>" in message
    assert "<updatedBy>TEST@UKRDC_FASTAPI</updatedBy>" in message


async def test_workitem_update(client):
    response = await client.put(
        f"{configuration.base_url}/v1/workitems/1/",
        json={"status": 3, "comment": "UPDATE COMMENT"},
    )
    assert response.status_code == 200
    assert response.json().get("status") == "success"

    message = response.json().get("message")

    assert "<workitem>1</workitem>" in message
    assert "<status>3</status>" in message
    assert "<updateDescription>UPDATE COMMENT</updateDescription>" in message
    assert "<updatedBy>TEST@UKRDC_FASTAPI</updatedBy>" in message
