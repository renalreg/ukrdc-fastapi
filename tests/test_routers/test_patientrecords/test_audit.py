from httpx import Response

from tests.conftest import PID_1, PID_2, PID_3, UKRDCID_1
from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.dependencies.audit import AuditOperation, Resource
from ukrdc_fastapi.schemas.audit import AuditEventSchema


def _extract_events(response: Response):
    assert response.status_code == 200
    return [AuditEventSchema(**item) for item in response.json().get("items")]


async def test_record_read_audit(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/{PID_1}"
    )
    assert response.status_code == 200

    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/{PID_1}/audit"
    )
    events = _extract_events(response)

    assert len(events) == 1


async def test_record_read_audit_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/{PID_3}/audit"
    )
    assert response.status_code == 403


async def test_record_results_read_audit(client_superuser):
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

    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/{PID_1}/audit?resource={Resource.RESULTITEMS.value}"
    )
    events = _extract_events(response)

    assert len(events) == 1

    event = events[0]

    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == PID_1

    assert len(event.children) == 1

    assert event.children[0].resource == "RESULTITEMS"
    assert event.children[0].operation == "READ"
    assert event.children[0].resource_id is None


async def test_record_pkb_membership_resource_audit(client_superuser):
    # Create a membership (twice, to test record-specific filtering)
    response = await client_superuser.post(
        f"{configuration.base_url}/ukrdcid/{UKRDCID_1}/memberships/create/pkb",
    )
    assert response.status_code == 200

    # Test audit patient and resource filtering

    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/{PID_1}/audit?resource={Resource.MEMBERSHIP.value}"
    )
    events = _extract_events(response)

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


async def test_record_create_operation_audit(client_superuser):
    # Create a membership (twice, to test record-specific filtering)
    response = await client_superuser.post(
        f"{configuration.base_url}/ukrdcid/{UKRDCID_1}/memberships/create/pkb",
    )
    assert response.status_code == 200

    # Test audit patient and resource filtering

    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/{PID_1}/audit?operation={AuditOperation.CREATE.value}"
    )
    events = _extract_events(response)

    assert len(events) == 1

    event = events[0]

    assert event.resource == "UKRDCID"
    assert event.operation == "READ"
    assert event.resource_id == UKRDCID_1

    assert len(event.children) == 1

    assert event.children[0].resource == "MEMBERSHIP"
    assert event.children[0].operation == "CREATE"
    assert event.children[0].resource_id == "PKB"
