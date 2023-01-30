import pytest
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person, PidXRef, WorkItem
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.query.delete import (
    ConfirmationError,
    delete_patientrecord,
    summarise_delete_patientrecord,
)

# We use "PYTEST03:PV:00000000A" as the pid to delete because it has no open workitems


def test_summarise_delete_pid_superuser(ukrdc3_session, jtrace_session, superuser):
    summary_1 = summarise_delete_patientrecord(
        ukrdc3_session, jtrace_session, "PYTEST03:PV:00000000A", superuser
    )

    summary_2 = summarise_delete_patientrecord(
        ukrdc3_session, jtrace_session, "PYTEST03:PV:00000000A", superuser
    )

    # Should get identical hash each request for the same delete
    assert summary_1.hash == summary_2.hash


def test_delete_pid_superuser(ukrdc3_session, jtrace_session, superuser):
    summary = summarise_delete_patientrecord(
        ukrdc3_session, jtrace_session, "PYTEST03:PV:00000000A", superuser
    )

    # Assert all expected records exist
    assert ukrdc3_session.query(PatientRecord).get("PYTEST03:PV:00000000A")
    for person in summary.empi.persons:
        assert jtrace_session.query(Person).get(person.id)
    for master_record in summary.empi.master_records:
        assert jtrace_session.query(MasterRecord).get(master_record.id)
    for pidxref in summary.empi.pidxrefs:
        assert jtrace_session.query(PidXRef).get(pidxref.id)
    for work_item in summary.empi.work_items:
        assert jtrace_session.query(WorkItem).get(work_item.id)
    for link_record in summary.empi.link_records:
        assert jtrace_session.query(LinkRecord).get(link_record.id)

    deleted = delete_patientrecord(
        ukrdc3_session, jtrace_session, "PYTEST03:PV:00000000A", summary.hash, superuser
    )

    assert deleted.hash == summary.hash

    # Assert all expected records have been deleted
    assert not ukrdc3_session.query(PatientRecord).get("PYTEST03:PV:00000000A")
    for person in summary.empi.persons:
        assert not jtrace_session.query(Person).get(person.id)
    for master_record in summary.empi.master_records:
        assert not jtrace_session.query(MasterRecord).get(master_record.id)
    for pidxref in summary.empi.pidxrefs:
        assert not jtrace_session.query(PidXRef).get(pidxref.id)
    for work_item in summary.empi.work_items:
        assert not jtrace_session.query(WorkItem).get(work_item.id)
    for link_record in summary.empi.link_records:
        assert not jtrace_session.query(LinkRecord).get(link_record.id)


def test_delete_pid_badhash(ukrdc3_session, jtrace_session, superuser):
    with pytest.raises(ConfirmationError):
        delete_patientrecord(
            ukrdc3_session,
            jtrace_session,
            "PYTEST03:PV:00000000A",
            "BADHASH",
            superuser,
        )


def test_summarise_delete_pid_denied(ukrdc3_session, jtrace_session, test_user):
    with pytest.raises(PermissionsError):
        summarise_delete_patientrecord(
            ukrdc3_session,
            jtrace_session,
            "PYTEST02:PV:00000000A",
            test_user,
        )


def test_delete_pid_denied(ukrdc3_session, jtrace_session, test_user):
    with pytest.raises(PermissionsError):
        delete_patientrecord(
            ukrdc3_session,
            jtrace_session,
            "PYTEST02:PV:00000000A",
            "RANDOMHASH",
            test_user,
        )
