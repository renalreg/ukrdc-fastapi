from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.query.memberships import (
    get_active_memberships_for_patientrecord,
    record_has_active_membership,
)


def test_get_active_memberships_for_patientrecord(ukrdc3_session):
    record = ukrdc3_session.get(PatientRecord, "PYTEST01:PV:00000000A")
    memberships = ukrdc3_session.scalars(get_active_memberships_for_patientrecord(record)).all()
    assert len(memberships) == 1
    assert memberships[0].program_name == "PROGRAM_NAME_1"


def test_record_has_active_membership_exists_active(ukrdc3_session):
    record = ukrdc3_session.get(PatientRecord, "PYTEST01:PV:00000000A")
    assert record_has_active_membership(ukrdc3_session, record, "PROGRAM_NAME_1")


def test_record_has_active_membership_exists_inactive(ukrdc3_session):
    record = ukrdc3_session.get(PatientRecord, "PYTEST01:PV:00000000A")
    assert not record_has_active_membership(ukrdc3_session, record, "PROGRAM_NAME_2")


def test_record_has_active_membership_notexists(ukrdc3_session):
    record = ukrdc3_session.get(PatientRecord, "PYTEST01:PV:00000000A")
    assert not record_has_active_membership(ukrdc3_session, record, "PROGRAM_NAME_X")
