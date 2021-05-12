import datetime

from ukrdc_fastapi.routers.api.errors import ExtendedErrorSchema
from ukrdc_fastapi.schemas.errors import MessageSchema


def test_errors_list(client):
    since = datetime.datetime(2020, 1, 1, 0, 0, 0).isoformat()
    until = datetime.datetime(2021, 12, 12, 23, 59, 59).isoformat()
    response = client.get(f"/api/errors/?since={since}&until={until}")
    assert response.status_code == 200
    messages = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in messages}
    assert returned_ids == {1, 2}


def test_errors_list_facility(client):
    since = datetime.datetime(2020, 1, 1, 0, 0, 0).isoformat()
    until = datetime.datetime(2021, 12, 12, 23, 59, 59).isoformat()
    response = client.get(
        f"/api/errors/?since={since}&until={until}&facility=MOCK_SENDING_FACILITY_1"
    )
    assert response.status_code == 200
    messages = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in messages}
    assert returned_ids == {2}


def test_errors_list_status(client):
    since = datetime.datetime(2020, 1, 1, 0, 0, 0).isoformat()
    until = datetime.datetime(2021, 12, 12, 23, 59, 59).isoformat()
    response = client.get(f"/api/errors/?since={since}&until={until}&status=ERROR2")
    assert response.status_code == 200
    messages = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in messages}
    assert returned_ids == {2}


def test_errors_detail(client):
    response = client.get("/api/errors/1")
    error = ExtendedErrorSchema(**response.json())
    assert error

    assert len(error.master_records) == 1
    assert error.master_records[0].id == 1

    assert len(error.work_items) == 2
    workitem_ids = {item.id for item in error.work_items}
    assert workitem_ids == {1, 2}
