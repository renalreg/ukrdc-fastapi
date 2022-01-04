from ukrdc_fastapi.schemas.message import MessageSchema

from ..utils import days_ago


def test_messages_list(client):
    since = days_ago(730).isoformat()
    until = days_ago(0).isoformat()
    response = client.get(f"/api/v1/messages/?since={since}&until={until}")
    assert response.status_code == 200
    messages = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in messages}
    assert returned_ids == {1, 2, 3}


def test_messages_list_errors(client):
    since = days_ago(730).isoformat()
    until = days_ago(0).isoformat()
    response = client.get(f"/api/v1/messages/?since={since}&until={until}&status=ERROR")
    assert response.status_code == 200
    messages = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in messages}
    assert returned_ids == {1, 2}


def test_messages_list_facility(client):
    since = days_ago(730).isoformat()
    until = days_ago(0).isoformat()
    response = client.get(
        f"/api/v1/messages/?since={since}&until={until}&facility=TEST_SENDING_FACILITY_2"
    )
    assert response.status_code == 200
    messages = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in messages}
    assert returned_ids == {2}


def test_message_detail(client):
    response = client.get("/api/v1/messages/1")
    assert response.status_code == 200
    error = MessageSchema(**response.json())
    assert error.id == 1


def test_message_workitems(client):
    response = client.get("/api/v1/messages/1/workitems")
    assert response.status_code == 200
    ids = {item.get("id") for item in response.json()}
    assert ids == set()

    response = client.get("/api/v1/messages/2/workitems")
    assert response.status_code == 200
    ids = {item.get("id") for item in response.json()}
    assert ids == {3}


def test_message_masterrecords(client):
    response = client.get("/api/v1/messages/1/masterrecords")
    assert response.status_code == 200
    ids = {item.get("id") for item in response.json()}
    assert ids == {1}
