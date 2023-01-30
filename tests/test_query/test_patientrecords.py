from datetime import datetime

import pytest

from tests.utils import create_basic_patient
from ukrdc_fastapi.query import patientrecords
from ukrdc_fastapi.query.common import PermissionsError


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


def test_get_patientrecords_from_ukrdcid_superuser(
    ukrdc3_session, jtrace_session, superuser
):
    _create_related_records(ukrdc3_session, jtrace_session)

    records = patientrecords.get_patientrecords_from_ukrdcid(
        ukrdc3_session, "999999511", superuser
    )
    assert {record.pid for record in records} == {
        "PYTEST02:TPR:TEST1",
        "PYTEST02:TPR:TEST2",
        "PYTEST02:TPR:TEST3",
        "PYTEST02:TPR:TEST4",
    }


def test_get_patientrecords_from_ukrdcid_user(
    ukrdc3_session, jtrace_session, test_user
):
    _create_related_records(ukrdc3_session, jtrace_session)

    records = patientrecords.get_patientrecords_from_ukrdcid(
        ukrdc3_session, "999999511", test_user
    )
    assert {record.pid for record in records} == {
        "PYTEST02:TPR:TEST1",
        "PYTEST02:TPR:TEST2",
        "PYTEST02:TPR:TEST4",
    }


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


def test_get_record_user_direct(ukrdc3_session, jtrace_session, test_user):
    # Direct permission to view record via sendingfacility
    _create_related_records(ukrdc3_session, jtrace_session)

    record = patientrecords.get_patientrecord(
        ukrdc3_session, "PYTEST02:TPR:TEST1", test_user
    )
    assert record
    assert record.pid == "PYTEST02:TPR:TEST1"


def test_get_record_user_direct_denied(ukrdc3_session, jtrace_session, test_user):
    # Direct permission to view record via sendingfacility
    _create_related_records(ukrdc3_session, jtrace_session)

    with pytest.raises(PermissionsError):
        patientrecords.get_patientrecord(
            ukrdc3_session, "PYTEST02:TPR:TEST3", test_user
        )


def test_get_record_user_indirect(ukrdc3_session, jtrace_session, test_user):
    # Indirect permissions, record sendingfacility is a multi-facility PKB membership

    _create_related_records(ukrdc3_session, jtrace_session)

    record = patientrecords.get_patientrecord(
        ukrdc3_session, "PYTEST02:TPR:TEST4", test_user
    )
    assert record
    assert record.pid == "PYTEST02:TPR:TEST4"


def test_record_related_superuser(ukrdc3_session, jtrace_session, superuser):
    # Create another record with the same UKRDCID
    _create_related_records(ukrdc3_session, jtrace_session)

    records = patientrecords.get_patientrecords_related_to_patientrecord(
        ukrdc3_session, "PYTEST02:TPR:TEST1", superuser
    )
    assert {record.pid for record in records} == {
        "PYTEST02:TPR:TEST1",
        "PYTEST02:TPR:TEST2",
        "PYTEST02:TPR:TEST3",
        "PYTEST02:TPR:TEST4",
    }


def test_record_related_user(ukrdc3_session, jtrace_session, test_user):
    # Create another record with the same UKRDCID
    _create_related_records(ukrdc3_session, jtrace_session)

    records = patientrecords.get_patientrecords_related_to_patientrecord(
        ukrdc3_session, "PYTEST02:TPR:TEST1", test_user
    )
    assert {record.pid for record in records} == {
        "PYTEST02:TPR:TEST1",
        "PYTEST02:TPR:TEST2",
        "PYTEST02:TPR:TEST4",
    }


def test_record_related_user_denied(ukrdc3_session, jtrace_session, test_user):
    # Create another record with the same UKRDCID
    _create_related_records(ukrdc3_session, jtrace_session)

    with pytest.raises(PermissionsError):
        patientrecords.get_patientrecords_related_to_patientrecord(
            ukrdc3_session, "PYTEST02:TPR:TEST3", test_user
        )


def test_get_patientrecords_related_to_masterrecord(
    ukrdc3_session, jtrace_session, superuser
):
    # Tests finding records related to multiple UKRDC IDs linked within JTRACE
    records = patientrecords.get_patientrecords_related_to_masterrecord(
        ukrdc3_session, jtrace_session, 1, superuser
    )

    assert {record.pid for record in records} == {
        "PYTEST01:PV:00000000A",
        "PYTEST04:PV:00000000A",
    }


def test_get_patientrecords_related_to_masterrecord_denied(
    ukrdc3_session, jtrace_session, test_user
):
    with pytest.raises(PermissionsError):
        patientrecords.get_patientrecords_related_to_masterrecord(
            ukrdc3_session, jtrace_session, 2, test_user
        )
