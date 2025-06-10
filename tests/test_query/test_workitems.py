from datetime import date, datetime

from ukrdc_sqla.empi import LinkRecord, MasterRecord, WorkItem
from ukrdc_sqla.errorsdb import Message

from tests.utils import days_ago
from ukrdc_fastapi.query import workitems


def test_get_workitems_superuser(jtrace_session):
    all_items = jtrace_session.scalars(workitems.select_workitems()).all()
    assert {item.id for item in all_items} == {1, 2, 3}


def test_get_workitems_facility(jtrace_session, superuser):
    all_items = jtrace_session.scalars(workitems.select_workitems(statuses=[3])).all()
    assert {item.id for item in all_items} == {4}


def test_get_workitems_statuses(jtrace_session):
    all_items = jtrace_session.scalars(
        workitems.select_workitems(statuses=[1, 3])
    ).all()
    assert {item.id for item in all_items} == {1, 2, 3, 4}


def test_get_workitems_since(jtrace_session):
    all_items = jtrace_session.scalars(
        workitems.select_workitems(since=days_ago(1))
    ).all()
    assert {item.id for item in all_items} == {2, 3}


def test_get_workitems_until(jtrace_session):
    all_items = jtrace_session.scalars(
        workitems.select_workitems(until=days_ago(2))
    ).all()
    assert {item.id for item in all_items} == {1}


def test_get_workitems_masterid(jtrace_session):
    all_items = jtrace_session.scalars(
        workitems.select_workitems(master_id=[104])
    ).all()
    assert {item.id for item in all_items} == {1, 2}


def test_get_workitem_related(jtrace_session):
    related = jtrace_session.scalars(
        workitems.select_workitems_related_to_workitem(
            jtrace_session.get(WorkItem, 1), jtrace_session
        )
    ).all()
    assert {item.id for item in related} == {2, 3, 4}

    related = jtrace_session.scalars(
        workitems.select_workitems_related_to_workitem(
            jtrace_session.get(WorkItem, 2), jtrace_session
        )
    ).all()
    assert {item.id for item in related} == {1, 3, 4}


def test_get_extended_workitem_superuser(jtrace_session):
    # Create a new master record
    master_record_999 = MasterRecord(
        id=999,
        status=0,
        lastupdated=days_ago(0),
        dateofbirth=datetime(1980, 12, 12),
        nationalid="119999999",
        nationalidtype="UKRDC",
        effectivedate=days_ago(0),
    )

    # Link the new master record to an existing person
    link_record_999 = LinkRecord(
        id=999,
        personid=1,
        masterid=999,
        linktype=0,
        linkcode=0,
        lastupdated=days_ago(0),
    )

    # Person 3 now has 2 master records we want to merge
    jtrace_session.add(master_record_999)
    jtrace_session.add(link_record_999)
    jtrace_session.commit()

    record = workitems.extend_workitem(jtrace_session.get(WorkItem, 1), jtrace_session)
    assert record
    assert record.id == 1

    assert record.incoming.person
    assert record.destination.master_record

    in_person = record.incoming.person.id
    in_masters = [master.id for master in record.incoming.master_records]
    dest_master = record.destination.master_record.id
    dest_persons = [person.id for person in record.destination.persons]

    assert in_person == 1
    assert in_masters == [1, 4, 999]
    assert dest_master == 104
    assert dest_persons == [4]


def test_get_workitem_collection(jtrace_session):
    collection = jtrace_session.scalars(
        workitems.select_workitem_collection(
            jtrace_session.get(WorkItem, 1), jtrace_session
        )
    ).all()
    assert {item.id for item in collection} == set()

    collection = jtrace_session.scalars(
        workitems.select_workitem_collection(
            jtrace_session.get(WorkItem, 2), jtrace_session
        )
    ).all()
    assert {item.id for item in collection} == {3, 4}


def test_get_workitems_related_to_message(jtrace_session, errorsdb_session):
    related = jtrace_session.scalars(
        workitems.select_workitems_related_to_message(
            errorsdb_session.get(Message, 3), jtrace_session
        )
    ).all()
    assert {item.id for item in related} == {3}


def test_get_full_workitem_history_default(jtrace_session):
    history = workitems.get_full_workitem_history(jtrace_session)
    d = {point.time: point.count for point in history}
    assert d[days_ago(1).date()] == 3


def test_get_full_workitem_history_all_time(jtrace_session):
    history = workitems.get_full_workitem_history(
        jtrace_session, since=date(1970, 1, 1)
    )
    d = {point.time: point.count for point in history}
    assert d[days_ago(365).date()] == 1
    assert d[days_ago(1).date()] == 3
