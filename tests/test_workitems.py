from datetime import datetime

import pytest
from ukrdc_sqla.empi import LinkRecord, MasterRecord, WorkItem

from ukrdc_fastapi.schemas.empi import WorkItemSchema


def test_workitems_list(client):
    response = client.get("/api/empi/workitems")
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1, 2, 3}


def test_workitems_list_ukrdcid_filter_single(client):
    response = client.get("/api/empi/workitems?ukrdcid=999999999")
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1, 2}


def test_workitems_list_ukrdcid_filter_multiple(client):
    response = client.get("/api/empi/workitems?ukrdcid=999999999&ukrdcid=999999911")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": 1,
            "links": {"self": "/api/empi/workitems/1"},
            "personId": 3,
            "masterId": 1,
            "type": 9,
            "description": "DESCRIPTION_1",
            "status": 1,
            "lastUpdated": "2020-03-16T00:00:00",
            "updatedBy": None,
            "updateDescription": None,
            "attributes": None,
        },
        {
            "id": 2,
            "links": {"self": "/api/empi/workitems/2"},
            "personId": 4,
            "masterId": 1,
            "type": 9,
            "description": "DESCRIPTION_2",
            "status": 1,
            "lastUpdated": "2021-01-01T00:00:00",
            "updatedBy": None,
            "updateDescription": None,
            "attributes": None,
        },
        {
            "id": 3,
            "links": {"self": "/api/empi/workitems/3"},
            "personId": 4,
            "masterId": 2,
            "type": 9,
            "description": "DESCRIPTION_3",
            "status": 1,
            "lastUpdated": "2021-01-01T00:00:00",
            "updatedBy": None,
            "updateDescription": None,
            "attributes": None,
        },
    ]


def test_workitem_detail(client):
    response = client.get("/api/empi/workitems/1")
    assert response.status_code == 200
    wi = WorkItemSchema(**response.json())
    assert wi.id == 1


def test_workitem_detail_not_found(client):
    response = client.get("/api/empi/workitems/9999")
    assert response.status_code == 404


@pytest.mark.parametrize("workitem_id", [1, 2, 3])
def test_workitem_close(client, workitem_id, mirth_session):
    with mirth_session:
        response = client.post(
            f"/api/empi/workitems/{workitem_id}/close",
            json={},
        )
    message = response.json().get("message")

    assert "<status>3</status>" in message
    assert f"<workitem>{workitem_id}</workitem>" in message
    assert "<updatedBy>TEST@UKRDC_FASTAPI</updatedBy>" in message


def test_workitem_close_not_found(client, mirth_session):
    with mirth_session:
        response = client.post(
            f"/api/empi/workitems/9999/close",
            json={},
        )
    assert response.status_code == 404


def test_workitem_merge(client, jtrace_session, mirth_session):

    # Create a new master record
    master_record_3 = MasterRecord(
        id=3,
        status=0,
        last_updated=datetime(2021, 1, 1),
        date_of_birth=datetime(1980, 12, 12),
        nationalid="119999999",
        nationalid_type="UKRDC",
        effective_date=datetime(2021, 1, 1),
    )

    # Link the new master record to an existing person
    link_record_3 = LinkRecord(
        id=3,
        person_id=1,
        master_id=3,
        link_type=0,
        link_code=0,
        last_updated=datetime(2020, 3, 16),
    )

    # Create a work item binding person 1 to master ID 3
    work_item_4 = WorkItem(
        id=4,
        person_id=1,
        master_id=3,
        type=9,
        description="DESCRIPTION_4",
        status=1,
        last_updated=datetime(2021, 1, 1),
    )

    # Person 3 now has 2 master records we want to merge
    jtrace_session.add(master_record_3)
    jtrace_session.add(link_record_3)
    jtrace_session.add(work_item_4)
    jtrace_session.commit()

    with mirth_session:
        response = client.post(f"/api/empi/workitems/4/merge", json={})
    assert response.json().get("status") == "success"
    message = response.json().get("message")

    # Check we are merging master records 1 and 3
    assert f"<superceding>1</superceding>" in message
    assert f"<superceeded>3</superceeded>" in message


def test_workitem_merge_nothing_to_merge(client, mirth_session):

    with mirth_session:
        response = client.post(f"/api/empi/workitems/1/merge", json={})

    # Expect a 400 error since only 1 master record is associated
    # with this work item, so nothing to merge
    assert response.status_code == 400


def test_workitem_merge_not_found(client, mirth_session):
    with mirth_session:
        response = client.post(f"/api/empi/workitems/9999/merge", json={})
    assert response.status_code == 404


@pytest.mark.parametrize("master_record", [1, 2])
@pytest.mark.parametrize("person_id", [1, 2, 3, 4])
@pytest.mark.parametrize("comment", [None, "", "COMMENT"])
def test_workitem_unlink(client, master_record, person_id, comment, mirth_session):
    with mirth_session:
        response = client.post(
            f"/api/empi/workitems/unlink",
            json={
                "master_record": master_record,
                "person_id": person_id,
                "comment": comment,
            },
        )

    assert response.json().get("status") == "success"
    message = response.json().get("message")

    assert f"<masterRecord>{master_record}</masterRecord>" in message
    assert f"<personId>{person_id}</personId>" in message
    assert "<updatedBy>TEST@UKRDC_FASTAPI</updatedBy>" in message
    if comment:
        assert f"<updateDescription>{comment}</updateDescription>" in message
    else:
        assert f"<updateDescription />" in message
