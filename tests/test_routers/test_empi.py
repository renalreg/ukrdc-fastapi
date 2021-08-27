from datetime import datetime

from ukrdc_sqla.empi import LinkRecord

from ukrdc_fastapi.schemas.empi import LinkRecordSchema


def test_merge(client, httpx_session):
    response = client.post(
        f"/api/v1/empi/merge/", json={"superseding": 1, "superseded": 2}
    )
    assert response.json().get("status") == "success"
    message = response.json().get("message")

    assert f"<superceding>1</superceding>" in message
    assert f"<superceeded>2</superceeded>" in message


def test_unlink(client, httpx_session, jtrace_session):
    # Create new link record
    link_999 = LinkRecord(
        id=999,
        person_id=3,
        master_id=1,
        link_type=0,
        link_code=0,
        last_updated=datetime(2019, 1, 1),
    )

    # Person 3 now has a link to Master Record 1
    jtrace_session.add(link_999)
    jtrace_session.commit()

    response = client.post(
        f"/api/v1/empi/unlink/",
        json={"personId": 3, "comment": "comment", "masterId": 1},
    )

    assert LinkRecordSchema(**response.json()) == LinkRecordSchema.from_orm(link_999)
