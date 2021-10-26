from datetime import date, datetime

import pytest
from ukrdc_sqla.empi import LinkRecord, MasterRecord

from ukrdc_fastapi.query import workitems
from ukrdc_fastapi.query.common import PermissionsError


def test_get_workitems_superuser(jtrace_session, superuser):
    all_items = workitems.get_workitems(jtrace_session, superuser)
    assert {item.id for item in all_items} == {1, 2, 3}


def test_get_workitems_user(jtrace_session, test_user):
    all_items = workitems.get_workitems(jtrace_session, test_user)
    assert {item.id for item in all_items} == {2, 3}


def test_get_workitems_facility(jtrace_session, superuser):
    all_items = workitems.get_workitems(jtrace_session, superuser, statuses=[3])
    assert {item.id for item in all_items} == {4}


def test_get_workitems_statuses(jtrace_session, superuser):
    all_items = workitems.get_workitems(
        jtrace_session, superuser, facility="TEST_SENDING_FACILITY_1"
    )
    assert {item.id for item in all_items} == {2, 3}


def test_get_workitems_since(jtrace_session, superuser):
    all_items = workitems.get_workitems(
        jtrace_session, superuser, since=datetime(2021, 1, 1)
    )
    assert {item.id for item in all_items} == {2, 3}


def test_get_workitems_until(jtrace_session, superuser):
    all_items = workitems.get_workitems(
        jtrace_session, superuser, until=datetime(2020, 12, 1)
    )
    assert {item.id for item in all_items} == {1}


def test_get_workitems_masterid(jtrace_session, superuser):
    all_items = workitems.get_workitems(jtrace_session, superuser, master_id=[1])
    assert {item.id for item in all_items} == {1, 2}


def test_get_workitem_superuser(jtrace_session, superuser):
    record = workitems.get_workitem(jtrace_session, 1, superuser)
    assert record
    assert record.id == 1


def test_get_workitem_user(jtrace_session, test_user):
    record = workitems.get_workitem(jtrace_session, 2, test_user)
    assert record
    assert record.id == 2


def test_get_workitem_denied(jtrace_session, test_user):
    with pytest.raises(PermissionsError):
        workitems.get_workitem(jtrace_session, 1, test_user)


def test_get_workitem_related(jtrace_session, superuser):
    related = workitems.get_workitems_related_to_workitem(jtrace_session, 1, superuser)
    assert {item.id for item in related} == {2, 4}

    related = workitems.get_workitems_related_to_workitem(jtrace_session, 2, superuser)
    assert {item.id for item in related} == {1, 3, 4}


def test_get_extended_workitem_superuser(jtrace_session, superuser):
    # Create a new master record
    master_record_999 = MasterRecord(
        id=999,
        status=0,
        last_updated=datetime(2021, 1, 1),
        date_of_birth=datetime(1980, 12, 12),
        nationalid="119999999",
        nationalid_type="UKRDC",
        effective_date=datetime(2021, 1, 1),
    )

    # Link the new master record to an existing person
    link_record_999 = LinkRecord(
        id=999,
        person_id=3,
        master_id=999,
        link_type=0,
        link_code=0,
        last_updated=datetime(2020, 3, 16),
    )

    # Person 3 now has 2 master records we want to merge
    jtrace_session.add(master_record_999)
    jtrace_session.add(link_record_999)
    jtrace_session.commit()

    record = workitems.get_extended_workitem(jtrace_session, 1, superuser)
    assert record
    assert record.id == 1

    in_person = record.incoming.person.id
    in_masters = [master.id for master in record.incoming.master_records]
    dest_master = record.destination.master_record.id
    dest_persons = [person.id for person in record.destination.persons]

    assert in_person == 3
    assert in_masters == [999]
    assert dest_master == 1
    assert dest_persons == [1, 2]


def test_get_workitem_collection(jtrace_session, superuser):
    collection = workitems.get_workitem_collection(jtrace_session, 1, superuser)
    assert {item.id for item in collection} == set()

    collection = workitems.get_workitem_collection(jtrace_session, 2, superuser)
    assert {item.id for item in collection} == {3, 4}


def test_get_workitems_related_to_message(jtrace_session, errorsdb_session, superuser):
    related = workitems.get_workitems_related_to_message(
        jtrace_session, errorsdb_session, 1, superuser
    )
    assert {item.id for item in related} == {1, 2}


def test_get_full_workitem_history_default(jtrace_session):
    history = workitems.get_full_workitem_history(jtrace_session)
    d = {point.time: point.count for point in history}
    assert d[date(2021, 1, 1)] == 3


def test_get_full_workitem_history_all_time(jtrace_session):
    history = workitems.get_full_workitem_history(
        jtrace_session, since=date(1970, 1, 1)
    )
    d = {point.time: point.count for point in history}
    assert d[date(2020, 3, 16)] == 1
    assert d[date(2021, 1, 1)] == 3
