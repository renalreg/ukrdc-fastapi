from datetime import datetime

from tests.utils import create_basic_patient
from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSchema


def _create_related_records(ukrdc3_session, jtrace_session):
    ukrdcid = "999999511"
    f1 = "TEST_SENDING_FACILITY_1"
    f2 = "TEST_SENDING_FACILITY_2"
    dob = datetime(1975, 10, 9)
    nhs = "888888885"
    localno = "00000000B"
    given = "GIVENNAME5"
    family = "FAMILYNAME5"

    # Basic record under facility 1
    create_basic_patient(
        105,
        "PYTEST02:TPR:TEST1",
        ukrdcid,
        nhs,
        f1,
        "UKRDC",
        localno,
        family,
        given,
        dob,
        ukrdc3_session,
        jtrace_session,
    )

    # Basic record under facility 1
    create_basic_patient(
        106,
        "PYTEST02:TPR:TEST2",
        ukrdcid,
        nhs,
        f1,
        "UKRDC",
        localno,
        family,
        given,
        dob,
        ukrdc3_session,
        jtrace_session,
    )

    # Basic record under facility 2
    create_basic_patient(
        107,
        "PYTEST02:TPR:TEST3",
        ukrdcid,
        nhs,
        f2,
        "UKRDC",
        localno,
        family,
        given,
        dob,
        ukrdc3_session,
        jtrace_session,
    )

    # PKB membership record
    create_basic_patient(
        108,
        "PYTEST02:TPR:TEST4",
        ukrdcid,
        nhs,
        "PKB",
        "UKRDC",
        localno,
        family,
        given,
        dob,
        ukrdc3_session,
        jtrace_session,
    )


async def test_get_record_superuser_direct(
    client_superuser, ukrdc3_session, jtrace_session
):
    # Direct permission to view record via sendingfacility
    _create_related_records(ukrdc3_session, jtrace_session)

    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST02:TPR:TEST1"
    )
    assert response.status_code == 200
    record = PatientRecordSchema(**response.json())
    assert record.pid == "PYTEST02:TPR:TEST1"


async def test_get_record_superuser_indirect(
    client_superuser, ukrdc3_session, jtrace_session
):
    # Indirect permissions, record sendingfacility is a multi-facility PKB membership
    _create_related_records(ukrdc3_session, jtrace_session)

    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST02:TPR:TEST4"
    )
    assert response.status_code == 200
    record = PatientRecordSchema(**response.json())
    assert record.pid == "PYTEST02:TPR:TEST4"


async def test_get_record_user_direct(
    client_authenticated, ukrdc3_session, jtrace_session
):
    # Direct permission to view record via sendingfacility
    _create_related_records(ukrdc3_session, jtrace_session)

    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST02:TPR:TEST1"
    )
    assert response.status_code == 200
    record = PatientRecordSchema(**response.json())
    assert record.pid == "PYTEST02:TPR:TEST1"


async def test_get_record_user_indirect(
    client_authenticated, ukrdc3_session, jtrace_session
):
    # Indirect permissions, record sendingfacility is a multi-facility PKB membership
    _create_related_records(ukrdc3_session, jtrace_session)

    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST02:TPR:TEST4"
    )
    assert response.status_code == 200
    record = PatientRecordSchema(**response.json())
    assert record.pid == "PYTEST02:TPR:TEST4"


async def test_get_record_user_direct_denied(
    client_authenticated, ukrdc3_session, jtrace_session
):
    # Direct permission to view record via sendingfacility denied
    _create_related_records(ukrdc3_session, jtrace_session)

    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST02:TPR:TEST3"
    )
    assert response.status_code == 403


async def test_record_missing(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:MISSING"
    )
    assert response.status_code == 404
