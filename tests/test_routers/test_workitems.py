from datetime import datetime

import pytest
from ukrdc_sqla.empi import LinkRecord, MasterRecord, WorkItem

from ukrdc_fastapi.schemas.empi import WorkItemSchema
from ukrdc_fastapi.schemas.errors import MessageSchema


def test_workitems_list(client):
    response = client.get("/api/v1/workitems")
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1, 2, 3}


def test_workitems_list_filter_since(client):
    response = client.get("/api/v1/workitems?since=2021-01-01T00:00:00")
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {2, 3}


def test_workitems_list_filter_until(client):
    response = client.get("/api/v1/workitems?until=2020-12-01T23:59:59")
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1}


def test_workitem_detail(client):
    response = client.get("/api/v1/workitems/1")
    assert response.status_code == 200
    wi = WorkItemSchema(**response.json())
    assert wi.id == 1


def test_workitem_related(client):
    response = client.get("/api/v1/workitems/1/related")
    assert response.status_code == 200

    returned_ids = {item["id"] for item in response.json()}
    assert returned_ids == {2}


def test_workitem_messages(client):
    response = client.get("/api/v1/workitems/1/messages")
    assert response.status_code == 200

    errors = [MessageSchema(**item) for item in response.json()["items"]]
    message_ids = {error.id for error in errors}
    assert message_ids == {1, 3}


def test_workitem_errors(client):
    response = client.get("/api/v1/workitems/1/messages/?status=ERROR")
    assert response.status_code == 200

    errors = [MessageSchema(**item) for item in response.json()["items"]]
    message_ids = {error.id for error in errors}
    assert message_ids == {1}


@pytest.mark.parametrize("workitem_id", [1, 2, 3])
def test_workitem_close(client, workitem_id, httpx_session):
    response = client.post(
        f"/api/v1/workitems/{workitem_id}/close/",
        json={},
    )
    message = response.json().get("message")

    assert "<status>3</status>" in message
    assert f"<workitem>{workitem_id}</workitem>" in message
    assert "<updatedBy>TEST@UKRDC_FASTAPI</updatedBy>" in message


def test_workitem_merge(client, jtrace_session, httpx_session):
    # Create a new master record
    master_record_30 = MasterRecord(
        id=30,
        status=0,
        last_updated=datetime(2021, 1, 1),
        date_of_birth=datetime(1980, 12, 12),
        nationalid="119999999",
        nationalid_type="UKRDC",
        effective_date=datetime(2021, 1, 1),
    )

    # Link the new master record to an existing person
    link_record_30 = LinkRecord(
        id=30,
        person_id=1,
        master_id=30,
        link_type=0,
        link_code=0,
        last_updated=datetime(2020, 3, 16),
    )

    # Create a work item binding person 1 to master ID 3
    work_item_40 = WorkItem(
        id=40,
        person_id=1,
        master_id=30,
        type=9,
        description="DESCRIPTION_4",
        status=1,
        last_updated=datetime(2021, 1, 1),
    )

    # Person 3 now has 2 master records we want to merge
    jtrace_session.add(master_record_30)
    jtrace_session.add(link_record_30)
    jtrace_session.add(work_item_40)
    jtrace_session.commit()

    response = client.post(f"/api/v1/workitems/40/merge/", json={})
    assert response.json().get("status") == "success"
    message = response.json().get("message")

    # Check we are merging master records 1 and 3
    assert f"<superceding>1</superceding>" in message
    assert f"<superceeded>30</superceeded>" in message


def test_workitem_merge_nothing_to_merge(client):
    response = client.post(f"/api/v1/workitems/1/merge/", json={})

    # Expect a 400 error since only 1 master record is associated
    # with this work item, so nothing to merge
    assert response.status_code == 400


def test_workitem_unlink(client, httpx_session):
    response = client.post(
        "/api/v1/workitems/1/unlink/",
    )

    assert response.json().get("status") == "success"
    message = response.json().get("message")

    assert f"<masterRecord>1</masterRecord>" in message
    assert f"<personId>3</personId>" in message
    assert "<updatedBy>TEST@UKRDC_FASTAPI</updatedBy>" in message
    assert f"<updateDescription />" in message


def test_workitem_update(client, httpx_session):
    response = client.put(
        "/api/v1/workitems/1/", json={"status": 3, "comment": "UPDATE COMMENT"}
    )

    assert response.json().get("status") == "success"
    message = response.json().get("message")

    assert "<workitem>1</workitem>" in message
    assert "<status>3</status>" in message
    assert "<updateDescription>UPDATE COMMENT</updateDescription>" in message
    assert "<updatedBy>TEST@UKRDC_FASTAPI</updatedBy>" in message
