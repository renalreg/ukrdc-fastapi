def test_merge(client, httpx_session):
    response = client.post(
        f"/api/v1/empi/merge/", json={"superseding": 1, "superseded": 2}
    )
    assert response.json().get("status") == "success"
    message = response.json().get("message")

    assert f"<superceding>1</superceding>" in message
    assert f"<superceeded>2</superceeded>" in message


def test_unlink(client, httpx_session):
    response = client.post(f"/api/v1/empi/unlink/", json={"personId": 1, "masterId": 1})
    assert response.json().get("status") == "success"
    message = response.json().get("message")

    assert f"<personId>1</personId>" in message
    assert f"<masterRecord>1</masterRecord>" in message


def test_unlink_patient(client, httpx_session):
    response = client.post(
        f"/api/v1/empi/unlink-patient/",
        json={"pid": "PYTEST02:PV:00000000A", "masterId": 2},
    )
    assert response.json().get("status") == "success"
    message = response.json().get("message")

    assert f"<personId>2</personId>" in message
    assert f"<masterRecord>2</masterRecord>" in message
