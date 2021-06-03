from datetime import datetime

import pytest
from ukrdc_sqla.empi import LinkRecord, MasterRecord

from ukrdc_fastapi.query import masterrecords
from ukrdc_fastapi.query.common import PermissionsError


def test_get_masterrecords_superuser(jtrace_session, superuser):
    all_records = masterrecords.get_masterrecords(jtrace_session, superuser)
    assert {record.id for record in all_records} == {1, 2}


def test_get_masterrecords_user(jtrace_session, test_user):
    all_records = masterrecords.get_masterrecords(jtrace_session, test_user)
    assert {record.id for record in all_records} == {1}


def test_get_masterrecords_facility(jtrace_session, superuser):
    all_records = masterrecords.get_masterrecords(
        jtrace_session, superuser, facility="TEST_SENDING_FACILITY_1"
    )
    assert {record.id for record in all_records} == {1}


def test_get_masterrecord_superuser(jtrace_session, superuser):
    record = masterrecords.get_masterrecord(jtrace_session, 1, superuser)
    assert record
    assert record.id == 1


def test_get_masterrecord_user(jtrace_session, test_user):
    record = masterrecords.get_masterrecord(jtrace_session, 1, test_user)
    assert record
    assert record.id == 1


def test_get_masterrecord_denied(jtrace_session, test_user):
    with pytest.raises(PermissionsError):
        masterrecords.get_masterrecord(jtrace_session, 2, test_user)


def test_masterrecord_related(jtrace_session, superuser):
    # Create a new master record
    master_record_3 = MasterRecord(
        id=3,
        status=0,
        last_updated=datetime(2021, 1, 1),
        date_of_birth=datetime(1980, 12, 12),
        nationalid="119999999",
        nationalid_type="UKRDC",
        effective_date=datetime(2021, 1, 1),
    )

    # Link the new master record to an existing person
    link_record_3 = LinkRecord(
        id=3,
        person_id=1,
        master_id=3,
        link_type=0,
        link_code=0,
        last_updated=datetime(2020, 3, 16),
    )

    # Person 3 now has 2 master records we want to merge
    jtrace_session.add(master_record_3)
    jtrace_session.add(link_record_3)
    jtrace_session.commit()

    records = masterrecords.get_masterrecords_related_to_masterrecord(
        jtrace_session, 1, superuser
    )

    # Check MR3 is identified as related to MR1
    assert {record.id for record in records} == {1, 3}
