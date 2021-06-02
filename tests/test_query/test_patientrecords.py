import pytest

from ukrdc_fastapi.query import patientrecords
from ukrdc_fastapi.query.common import PermissionsError


def test_get_records_superuser(ukrdc3_session, superuser):
    all_records = patientrecords.get_patientrecords(ukrdc3_session, superuser)
    assert {record.pid for record in all_records} == {
        "PYTEST01:PV:00000000A",
        "PYTEST02:PV:00000000A",
    }


def test_get_records_user(ukrdc3_session, test_user):
    all_records = patientrecords.get_patientrecords(ukrdc3_session, test_user)
    assert {record.pid for record in all_records} == {"PYTEST01:PV:00000000A"}


def test_get_record_superuser(ukrdc3_session, superuser):
    record = patientrecords.get_patientrecord(
        ukrdc3_session, "PYTEST01:PV:00000000A", superuser
    )
    assert record
    assert record.pid == "PYTEST01:PV:00000000A"


def test_get_record_user(ukrdc3_session, test_user):
    record = patientrecords.get_patientrecord(
        ukrdc3_session, "PYTEST01:PV:00000000A", test_user
    )
    assert record
    assert record.pid == "PYTEST01:PV:00000000A"


def test_get_record_denied(ukrdc3_session, test_user):
    with pytest.raises(PermissionsError):
        patientrecords.get_patientrecord(
            ukrdc3_session, "PYTEST02:PV:00000000A", test_user
        )


def test_record_related(ukrdc3_session, jtrace_session, superuser):
    records = patientrecords.get_patientrecords_related_to_patientrecord(
        ukrdc3_session, jtrace_session, "PYTEST01:PV:00000000A", superuser
    )
    assert {record.pid for record in records} == {
        "PYTEST01:PV:00000000A",
        "PYTEST02:PV:00000000A",
    }
