from datetime import datetime

from ukrdc_sqla.ukrdc import LabOrder, ResultItem

from ukrdc_fastapi.models.audit import AuditEvent


def test_record_read_audit(client, audit_session):
    path = "/api/v1/patientrecords/PYTEST01:PV:00000000A/"
    response = client.get(path)
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 1

    event = events[0]
    assert len(event.children) == 0

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None


def test_record_delete_summary_audit(client, audit_session):
    response = client.post("/api/v1/patientrecords/PYTEST03:PV:00000000A/delete")
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 4

    # All events should be related to the primary event
    primary_event = events[0]
    assert len(primary_event.children) == 3

    # Check all event types
    for event in events:
        assert event.operation == "READ"

    child_event_summaries = [
        (child.resource, child.resource_id) for child in primary_event.children
    ]

    assert ("PERSON", "3") in child_event_summaries
    assert ("MASTER_RECORD", "3") in child_event_summaries
    assert ("MASTER_RECORD", "103") in child_event_summaries


def test_record_delete_audit(client, audit_session):
    response = client.post("/api/v1/patientrecords/PYTEST03:PV:00000000A/delete")
    assert response.status_code == 200

    deleted_response = client.post(
        "/api/v1/patientrecords/PYTEST03:PV:00000000A/delete",
        json={"hash": response.json().get("hash")},
    )

    assert deleted_response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 8

    # We get 4 events for the delete summary and 4 for the actual delete

    # All events should be related to the primary event
    primary_event = events[4]
    assert len(primary_event.children) == 3

    # Check all event types
    for event in events[4:]:
        assert event.operation == "DELETE"

    child_event_summaries = [
        (child.resource, child.resource_id) for child in primary_event.children
    ]

    assert ("PERSON", "3") in child_event_summaries
    assert ("MASTER_RECORD", "3") in child_event_summaries
    assert ("MASTER_RECORD", "103") in child_event_summaries


def test_record_read_medications(client, audit_session):
    response = client.get("/api/v1/patientrecords/PYTEST01:PV:00000000A/medications")
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "MEDICATIONS"
    assert child_event.operation == "READ"
    assert child_event.resource_id == None
    assert child_event.parent_id == event.id


def test_record_read_treatments(client, audit_session):
    response = client.get("/api/v1/patientrecords/PYTEST01:PV:00000000A/treatments")
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "TREATMENTS"
    assert child_event.operation == "READ"
    assert child_event.resource_id == None
    assert child_event.parent_id == event.id


def test_record_read_surveys(client, audit_session):
    response = client.get("/api/v1/patientrecords/PYTEST01:PV:00000000A/surveys")
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "SURVEYS"
    assert child_event.operation == "READ"
    assert child_event.resource_id == None
    assert child_event.parent_id == event.id


def test_record_read_observations(client, audit_session):
    response = client.get("/api/v1/patientrecords/PYTEST01:PV:00000000A/observations")
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "OBSERVATIONS"
    assert child_event.operation == "READ"
    assert child_event.resource_id == None
    assert child_event.parent_id == event.id


def test_record_read_laborders(client, audit_session):
    response = client.get("/api/v1/patientrecords/PYTEST01:PV:00000000A/laborders")
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "LABORDERS"
    assert child_event.operation == "READ"
    assert child_event.resource_id == None
    assert child_event.parent_id == event.id


def test_record_read_laborder(client, audit_session):
    response = client.get(
        "/api/v1/patientrecords/PYTEST01:PV:00000000A/laborders/LABORDER1"
    )
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "LABORDER"
    assert child_event.operation == "READ"
    assert child_event.resource_id == "LABORDER1"
    assert child_event.parent_id == event.id


def test_record_delete_laborder(client, ukrdc3_session, audit_session):
    laborder = LabOrder(
        id="LABORDER_TEMP",
        pid="PYTEST01:PV:00000000A",
        external_id="EXTERNAL_ID_TEMP",
        order_category="ORDER_CATEGORY_TEMP",
        specimen_collected_time=datetime(2020, 3, 16),
    )
    resultitem = ResultItem(
        id="RESULTITEM_TEMP",
        order_id="LABORDER_TEMP",
        service_id_std="SERVICE_ID_STD_TEMP",
        service_id="SERVICE_ID_TEMP",
        service_id_description="SERVICE_ID_DESCRIPTION_TEMP",
        value="VALUE_TEMP",
        value_units="VALUE_UNITS_TEMP",
        observation_time=datetime(2020, 3, 16),
    )
    ukrdc3_session.add(laborder)
    ukrdc3_session.add(resultitem)
    ukrdc3_session.commit()

    # Make sure the laborder was created
    assert ukrdc3_session.query(LabOrder).get("LABORDER_TEMP")
    assert ukrdc3_session.query(ResultItem).get("RESULTITEM_TEMP")

    response = client.delete(
        "/api/v1/patientrecords/PYTEST01:PV:00000000A/laborders/LABORDER_TEMP/"
    )
    assert response.status_code == 204

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 3

    record_event = events[0]
    assert len(record_event.children) == 1

    assert record_event.resource == "PATIENT_RECORD"
    assert record_event.operation == "UPDATE"
    assert record_event.resource_id == "PYTEST01:PV:00000000A"
    assert record_event.parent_id == None

    order_event = record_event.children[0]
    assert len(order_event.children) == 1

    assert order_event.resource == "LABORDER"
    assert order_event.operation == "DELETE"
    assert order_event.resource_id == "LABORDER_TEMP"
    assert order_event.parent_id == record_event.id

    result_event = order_event.children[0]
    assert len(result_event.children) == 0

    assert result_event.resource == "RESULTITEM"
    assert result_event.operation == "DELETE"
    assert result_event.resource_id == "RESULTITEM_TEMP"
    assert result_event.parent_id == order_event.id


def test_record_read_resultitems(client, audit_session):
    response = client.get("/api/v1/patientrecords/PYTEST01:PV:00000000A/results")
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "RESULTITEMS"
    assert child_event.operation == "READ"
    assert child_event.resource_id == None
    assert child_event.parent_id == event.id


def test_record_read_resultitem(client, audit_session):
    response = client.get(
        "/api/v1/patientrecords/PYTEST01:PV:00000000A/results/RESULTITEM1"
    )
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "RESULTITEM"
    assert child_event.operation == "READ"
    assert child_event.resource_id == "RESULTITEM1"
    assert child_event.parent_id == event.id


def test_record_delete_resultitem(client, audit_session):
    response = client.delete(
        "/api/v1/patientrecords/PYTEST01:PV:00000000A/results/RESULTITEM1/"
    )
    assert response.status_code == 204

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "UPDATE"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "RESULTITEM"
    assert child_event.operation == "DELETE"
    assert child_event.resource_id == "RESULTITEM1"
    assert child_event.parent_id == event.id


def test_record_read_documents(client, audit_session):
    response = client.get("/api/v1/patientrecords/PYTEST01:PV:00000000A/documents")
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "DOCUMENTS"
    assert child_event.operation == "READ"
    assert child_event.resource_id == None
    assert child_event.parent_id == event.id


def test_record_read_document(client, audit_session):
    response = client.get(
        "/api/v1/patientrecords/PYTEST01:PV:00000000A/documents/DOCUMENT_PDF"
    )
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "DOCUMENT"
    assert child_event.operation == "READ"
    assert child_event.resource_id == "DOCUMENT_PDF"
    assert child_event.parent_id == event.id


def test_record_download_document(client, audit_session):
    response = client.get(
        "/api/v1/patientrecords/PYTEST01:PV:00000000A/documents/DOCUMENT_PDF/download"
    )
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "DOCUMENT"
    assert child_event.operation == "READ"
    assert child_event.resource_id == "DOCUMENT_PDF"
    assert child_event.parent_id == event.id


def test_record_export_data(client, audit_session):
    response = client.post(
        "/api/v1/patientrecords/PYTEST01:PV:00000000A/export/pv/", json={}
    )
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 1

    event = events[0]
    assert len(event.children) == 0

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "EXPORT_PV"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None


def test_record_export_tests(client, audit_session):
    response = client.post(
        "/api/v1/patientrecords/PYTEST01:PV:00000000A/export/pv-tests/", json={}
    )
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 1

    event = events[0]
    assert len(event.children) == 0

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "EXPORT_PV_TESTS"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None


def test_record_export_docs(client, audit_session):
    response = client.post(
        "/api/v1/patientrecords/PYTEST01:PV:00000000A/export/pv-docs/", json={}
    )
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 1

    event = events[0]
    assert len(event.children) == 0

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "EXPORT_PV_DOCS"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None


def test_record_export_radar(client, audit_session):
    response = client.post(
        "/api/v1/patientrecords/PYTEST01:PV:00000000A/export/radar/", json={}
    )
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 1

    event = events[0]
    assert len(event.children) == 0

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "EXPORT_RADAR"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None