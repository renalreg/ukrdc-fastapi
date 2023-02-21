from datetime import datetime

from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.ukrdc import PatientRecord

from tests.utils import create_basic_patient
from ukrdc_fastapi.query import patientrecords


def _create_related_records(ukrdc3_session, jtrace_session):
    ukrdcid = "999999511"
    f1 = "TSF01"
    f2 = "TSF02"
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


def test_get_patientrecords_related_to_patientrecord(ukrdc3_session, jtrace_session):
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
    _create_related_records(ukrdc3_session, jtrace_session)

    records = patientrecords.get_patientrecords_related_to_masterrecord(
        jtrace_session.query(MasterRecord).get(105), ukrdc3_session, jtrace_session
    )

    assert {record.pid for record in records} == {
        "PYTEST02:TPR:TEST1",
        "PYTEST02:TPR:TEST2",
        "PYTEST02:TPR:TEST3",
        "PYTEST02:TPR:TEST4",
    }
