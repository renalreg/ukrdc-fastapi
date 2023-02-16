from datetime import datetime

import pytest
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.ukrdc import PatientRecord

from tests.utils import create_basic_patient
from ukrdc_fastapi.query import patientrecords


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


"""
PERMISSION TESTS - REUSE LOGIC LATER
def test_get_record_superuser_direct(ukrdc3_session, jtrace_session, superuser):
    # Direct permission to view record via sendingfacility
    _create_related_records(ukrdc3_session, jtrace_session)

    record = patientrecords.get_patientrecord(
        ukrdc3_session, "PYTEST02:TPR:TEST1", superuser
    )
    assert record
    assert record.pid == "PYTEST02:TPR:TEST1"


def test_get_record_superuser_indirect(ukrdc3_session, jtrace_session, superuser):
    # Indirect permissions, record sendingfacility is a multi-facility PKB membership

    _create_related_records(ukrdc3_session, jtrace_session)

    record = patientrecords.get_patientrecord(
        ukrdc3_session, "PYTEST02:TPR:TEST4", superuser
    )
    assert record
    assert record.pid == "PYTEST02:TPR:TEST4"


def test_get_record_user_direct(ukrdc3_session, jtrace_session, user):
    # Direct permission to view record via sendingfacility
    _create_related_records(ukrdc3_session, jtrace_session)

    record = patientrecords.get_patientrecord(
        ukrdc3_session, "PYTEST02:TPR:TEST1", user
    )
    assert record
    assert record.pid == "PYTEST02:TPR:TEST1"


def test_get_record_user_direct_denied(ukrdc3_session, jtrace_session, user):
    # Direct permission to view record via sendingfacility
    _create_related_records(ukrdc3_session, jtrace_session)

    with pytest.raises(PermissionsError):
        patientrecords.get_patientrecord(
            ukrdc3_session, "PYTEST02:TPR:TEST3", user
        )


def test_get_record_user_indirect(ukrdc3_session, jtrace_session, user):
    # Indirect permissions, record sendingfacility is a multi-facility PKB membership

    _create_related_records(ukrdc3_session, jtrace_session)

    record = patientrecords.get_patientrecord(
        ukrdc3_session, "PYTEST02:TPR:TEST4", user
    )
    assert record
    assert record.pid == "PYTEST02:TPR:TEST4"
"""


def test_get_patientrecords_related_to_patientrecord(ukrdc3_session, jtrace_session):
    # Create another record with the same UKRDCID
    _create_related_records(ukrdc3_session, jtrace_session)

    records = patientrecords.get_patientrecords_related_to_patientrecord(
        ukrdc3_session.query(PatientRecord).get("PYTEST02:TPR:TEST1"), ukrdc3_session
    )
    assert {record.pid for record in records} == {
        "PYTEST02:TPR:TEST1",
        "PYTEST02:TPR:TEST2",
        "PYTEST02:TPR:TEST3",
        "PYTEST02:TPR:TEST4",
    }


def test_get_patientrecords_related_to_masterrecord(ukrdc3_session, jtrace_session):
    # Tests finding records related to multiple UKRDC IDs linked within JTRACE
    records = patientrecords.get_patientrecords_related_to_masterrecord(
        jtrace_session.query(MasterRecord).get(1), ukrdc3_session, jtrace_session
    )

    assert {record.pid for record in records} == {
        "PYTEST01:PV:00000000A",
        "PYTEST04:PV:00000000A",
    }
