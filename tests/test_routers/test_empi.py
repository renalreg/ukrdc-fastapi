from ukrdc_fastapi.config import configuration


def test_merge(client, httpx_session):
    response = client.post(
        f"{configuration.base_url}/v1/empi/merge/",
        json={"superseding": 1, "superseded": 2},
    )
    assert response.json().get("status") == "success"
    message = response.json().get("message")

    assert f"<superceding>1</superceding>" in message
    assert f"<superceeded>2</superceeded>" in message


def test_unlink(client, httpx_session, jtrace_session):
    response = client.post(
        f"{configuration.base_url}/v1/empi/unlink/",
        json={"personId": 4, "comment": "comment", "masterId": 1},
    )

    assert response.json().get("id") == 4
