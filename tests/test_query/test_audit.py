from tests.conftest import PID_1, PID_2, UKRDCID_1, UKRDCID_2
from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.dependencies.audit import AuditOperation, Resource
from ukrdc_sqla.ukrdc import PatientRecord
from ukrdc_fastapi.query.audit import get_auditevents_related_to_patientrecord


async def test_record_read_audit(
    client_superuser,
    ukrdc3_session,
    audit_session,
):
    # View a record (twice, to test record-specific filtering)
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/{PID_1}"
    )
    assert response.status_code == 200

    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/{PID_2}"
    )
    assert response.status_code == 200

    # Test audit patient filtering

    events = get_auditevents_related_to_patientrecord(
        ukrdc3_session.query(PatientRecord).get(PID_1), audit_session
    ).all()

    assert len(events) == 1

    event = events[0]
    assert len(event.children) == 0

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == PID_1
    assert event.parent_id is None


async def test_record_results_read_audit(
    client_superuser,
    ukrdc3_session,
    audit_session,
):
    # View a record (twice, to test record-specific filtering)
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/{PID_1}/results"
    )
    assert response.status_code == 200

    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/{PID_2}/results"
    )
    assert response.status_code == 200

    # Test audit patient filtering

    events = get_auditevents_related_to_patientrecord(
        ukrdc3_session.query(PatientRecord).get(PID_1),
        audit_session,
        resource=Resource.RESULTITEMS,
    ).all()

    assert len(events) == 1

    event = events[0]

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == PID_1

    assert len(event.children) == 1

    assert event.children[0].resource == "RESULTITEMS"
    assert event.children[0].operation == "READ"
    assert event.children[0].resource_id is None


async def test_record_pkb_membership_resource_audit(
    client_superuser,
    ukrdc3_session,
    audit_session,
):
    # Create a membership (twice, to test record-specific filtering)
    response = await client_superuser.post(
        f"{configuration.base_url}/ukrdcid/{UKRDCID_1}/memberships/create/pkb",
    )
    assert response.status_code == 200

    response = await client_superuser.post(
        f"{configuration.base_url}/ukrdcid/{UKRDCID_2}/memberships/create/pkb",
    )
    assert response.status_code == 200

    # Test audit patient and resource filtering

    events = get_auditevents_related_to_patientrecord(
        ukrdc3_session.query(PatientRecord).get(PID_1),
        audit_session,
        resource=Resource.MEMBERSHIP,
    ).all()

    # One for viewing the record (PID), another for creating the membership (UKRDCID -> MEMBERSHIP)
    assert len(events) == 1

    event = events[0]

    assert event.resource == "UKRDCID"
    assert event.operation == "READ"
    assert event.resource_id == UKRDCID_1

    assert len(event.children) == 1

    assert event.children[0].resource == "MEMBERSHIP"
    assert event.children[0].operation == "CREATE"
    assert event.children[0].resource_id == "PKB"


async def test_record_create_operation_audit(
    client_superuser,
    ukrdc3_session,
    audit_session,
):
    # Create a membership (twice, to test record-specific filtering)
    response = await client_superuser.post(
        f"{configuration.base_url}/ukrdcid/{UKRDCID_1}/memberships/create/pkb",
    )
    assert response.status_code == 200

    response = await client_superuser.post(
        f"{configuration.base_url}/ukrdcid/{UKRDCID_2}/memberships/create/pkb",
    )
    assert response.status_code == 200

    # Test audit patient and resource filtering

    events = get_auditevents_related_to_patientrecord(
        ukrdc3_session.query(PatientRecord).get(PID_1),
        audit_session,
        operation=AuditOperation.CREATE,
    ).all()

    # One for viewing the record (PID), another for creating the membership (UKRDCID -> MEMBERSHIP)
    assert len(events) == 1

    event = events[0]

    assert event.resource == "UKRDCID"
    assert event.operation == "READ"
    assert event.resource_id == UKRDCID_1

    assert len(event.children) == 1

    assert event.children[0].resource == "MEMBERSHIP"
    assert event.children[0].operation == "CREATE"
    assert event.children[0].resource_id == "PKB"
