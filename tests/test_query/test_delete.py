import pytest
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person, PidXRef, WorkItem
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.query.delete import (
    ConfirmationError,
    delete_patientrecord,
    summarise_delete_patientrecord,
)

# We use "PYTEST03:PV:00000000A" as the pid to delete because it has no open workitems


def test_summarise_delete_pid_superuser(ukrdc3_session, jtrace_session):
    record_to_delete = ukrdc3_session.get(PatientRecord, "PYTEST03:PV:00000000A")

    summary_1 = summarise_delete_patientrecord(record_to_delete, jtrace_session)
    summary_2 = summarise_delete_patientrecord(record_to_delete, jtrace_session)

    # Should get identical hash each request for the same delete
    assert summary_1.hash == summary_2.hash


def test_delete_pid_superuser(ukrdc3_session, jtrace_session):
    record_to_delete = ukrdc3_session.get(PatientRecord, "PYTEST03:PV:00000000A")

    summary = summarise_delete_patientrecord(record_to_delete, jtrace_session)

    # Assert all expected records exist
    assert ukrdc3_session.get(PatientRecord, "PYTEST03:PV:00000000A")

    assert summary.empi
    for person in summary.empi.persons:
        assert jtrace_session.get(Person, person.id)
    for master_record in summary.empi.master_records:
        assert jtrace_session.get(MasterRecord, master_record.id)
    for pidxref in summary.empi.pidxrefs:
        assert jtrace_session.get(PidXRef, pidxref.id)
    for work_item in summary.empi.work_items:
        assert jtrace_session.get(WorkItem, work_item.id)
    for link_record in summary.empi.link_records:
        assert jtrace_session.get(LinkRecord, link_record.id)

    deleted = delete_patientrecord(
        record_to_delete, ukrdc3_session, jtrace_session, summary.hash
    )

    assert deleted.hash == summary.hash

    # Assert all expected records have been deleted
    assert not ukrdc3_session.get(PatientRecord, "PYTEST03:PV:00000000A")
    for person in summary.empi.persons:
        assert not jtrace_session.get(Person, person.id)
    for master_record in summary.empi.master_records:
        assert not jtrace_session.get(MasterRecord, master_record.id)
    for pidxref in summary.empi.pidxrefs:
        assert not jtrace_session.get(PidXRef, pidxref.id)
    for work_item in summary.empi.work_items:
        assert not jtrace_session.get(WorkItem, work_item.id)
    for link_record in summary.empi.link_records:
        assert not jtrace_session.get(LinkRecord, link_record.id)


def test_delete_pid_badhash(ukrdc3_session, jtrace_session):
    record_to_delete = ukrdc3_session.get(PatientRecord, "PYTEST03:PV:00000000A")

    with pytest.raises(ConfirmationError):
        delete_patientrecord(
            record_to_delete,
            ukrdc3_session,
            jtrace_session,
            "BADHASH",
        )
