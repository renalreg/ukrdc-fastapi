def test_merge(client, httpx_session):
    response = client.post(
        f"/api/v1/empi/merge/", json={"superceding": 1, "superceeded": 2}
    )
    assert response.json().get("status") == "success"
    message = response.json().get("message")

    # Check we are merging master records 1 and 3
    assert f"<superceding>1</superceding>" in message
    assert f"<superceeded>2</superceeded>" in message


def test_unlink(client, httpx_session):
    response = client.post(f"/api/v1/empi/unlink/", json={"personId": 1, "masterId": 1})
    assert response.json().get("status") == "success"
    message = response.json().get("message")

    # Check we are merging master records 1 and 3
    assert f"<personId>1</personId>" in message
    assert f"<masterRecord>1</masterRecord>" in message
