from datetime import datetime

import pytest

from ukrdc_fastapi.models.empi import LinkRecord, MasterRecord, WorkItem


def test_workitems_list(client):
    response = client.get("/workitems")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": 1,
            "person_id": 3,
            "master_id": 1,
            "type": 9,
            "description": "DESCRIPTION_1",
            "status": 1,
            "last_updated": "2020-03-16T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
        {
            "id": 2,
            "person_id": 4,
            "master_id": 1,
            "type": 9,
            "description": "DESCRIPTION_2",
            "status": 1,
            "last_updated": "2021-01-01T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
        {
            "id": 3,
            "person_id": 4,
            "master_id": 2,
            "type": 9,
            "description": "DESCRIPTION_3",
            "status": 1,
            "last_updated": "2021-01-01T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
    ]


def test_workitems_list_ukrdcid_filter_single(client):
    response = client.get("/workitems?ukrdcid=999999999")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": 1,
            "person_id": 3,
            "master_id": 1,
            "type": 9,
            "description": "DESCRIPTION_1",
            "status": 1,
            "last_updated": "2020-03-16T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
        {
            "id": 2,
            "person_id": 4,
            "master_id": 1,
            "type": 9,
            "description": "DESCRIPTION_2",
            "status": 1,
            "last_updated": "2021-01-01T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
    ]


def test_workitems_list_ukrdcid_filter_multiple(client):
    response = client.get("/workitems?ukrdcid=999999999&ukrdcid=999999911")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": 1,
            "person_id": 3,
            "master_id": 1,
            "type": 9,
            "description": "DESCRIPTION_1",
            "status": 1,
            "last_updated": "2020-03-16T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
        {
            "id": 2,
            "person_id": 4,
            "master_id": 1,
            "type": 9,
            "description": "DESCRIPTION_2",
            "status": 1,
            "last_updated": "2021-01-01T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
        {
            "id": 3,
            "person_id": 4,
            "master_id": 2,
            "type": 9,
            "description": "DESCRIPTION_3",
            "status": 1,
            "last_updated": "2021-01-01T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
    ]


def test_workitem_detail(client):
    response = client.get("/workitems/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "person_id": 3,
        "master_id": 1,
        "type": 9,
        "description": "DESCRIPTION_1",
        "status": 1,
        "last_updated": "2020-03-16T00:00:00",
        "updated_by": None,
        "update_description": None,
        "attributes": None,
        "person": {
            "id": 3,
            "originator": "UKRDC",
            "localid": "192837465",
            "localid_type": "CLPID",
            "date_of_birth": "1950-01-01",
            "gender": "9",
            "date_of_death": None,
            "givenname": None,
            "surname": None,
            "xref_entries": [],
        },
        "master_record": {
            "id": 1,
            "last_updated": "2020-03-16T00:00:00",
            "date_of_birth": "1950-01-01",
            "gender": None,
            "givenname": None,
            "surname": None,
            "nationalid": "999999999",
            "nationalid_type": "UKRDC",
            "status": 0,
            "effective_date": "2020-03-16T00:00:00",
        },
        "related": [
            {
                "id": 2,
                "person_id": 4,
                "master_id": 1,
            }
        ],
    }


def test_workitem_detail_not_found(client):
    response = client.get("/workitems/9999")
    assert response.status_code == 404


@pytest.mark.parametrize("workitem_id", [1, 2, 3])
def test_workitem_close(client, workitem_id):
    response = client.post(
        f"/workitems/{workitem_id}/close",
        json={"mirth": False},
    )
    assert response.json().get("status") == "ignored"
    message = response.json().get("message")

    assert "<status>3</status>" in message
    assert f"<workitem>{workitem_id}</workitem>" in message


def test_workitem_close_not_found(client):
    response = client.post(
        f"/workitems/9999/close",
        json={"mirth": False},
    )
    assert response.status_code == 404


def test_workitem_merge(client, jtrace_session):

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

    response = client.post(
        f"/workitems/4/merge",
        json={"mirth": False},
    )
    assert response.json().get("status") == "ignored"
    message = response.json().get("message")

    # Check we are merging master records 1 and 3
    assert f"<superceding>1</superceding>" in message
    assert f"<superceeded>3</superceeded>" in message


def test_workitem_merge_nothing_to_merge(client):

    response = client.post(
        f"/workitems/1/merge",
        json={"mirth": False},
    )

    # Expect a 400 error since only 1 master record is associated
    # with this work item, so nothing to merge
    assert response.status_code == 400


def test_workitem_merge_not_found(client):
    response = client.post(
        f"/workitems/9999/merge",
        json={"mirth": False},
    )
    assert response.status_code == 404


@pytest.mark.parametrize("master_record", [1, 2])
@pytest.mark.parametrize("person_id", [1, 2, 3, 4])
@pytest.mark.parametrize("comment", [None, "", "COMMENT"])
def test_workitem_unlink(client, master_record, person_id, comment):
    response = client.post(
        f"/workitems/unlink",
        json={
            "master_record": master_record,
            "person_id": person_id,
            "comment": comment,
            "mirth": False,
        },
    )

    assert response.json().get("status") == "ignored"
    message = response.json().get("message")

    assert f"<masterRecord>{master_record}</masterRecord >" in message
    assert f"<personId>{person_id}</personId>" in message
    if comment:
        assert f"<updateDescription>{comment}</updateDescription>" in message
    else:
        assert f"<updateDescription></updateDescription>" in message
