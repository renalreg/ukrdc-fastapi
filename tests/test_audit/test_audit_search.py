from ukrdc_fastapi.models.audit import AuditEvent


def test_search_pid(client, audit_session):
    response = client.get(f"/api/v1/search/?search=999999999&include_ukrdc=true")
    assert response.status_code == 200

    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {104, 1, 4, 101}

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 4

    for event in events:
        assert event.resource == "MASTER_RECORD"
        assert event.operation == "READ"
        assert int(event.resource_id) in returned_ids
        assert event.parent_id == None
