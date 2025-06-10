import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import or_
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.selectable import Select
from ukrdc_sqla.empi import MasterRecord, Person, PidXRef, WorkItem
from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.utils.links import find_related_ids

from ukrdc_fastapi.query.masterrecords import select_masterrecords_related_to_person
from ukrdc_fastapi.query.persons import select_persons_related_to_masterrecord
from ukrdc_fastapi.schemas.common import HistoryPoint
from ukrdc_fastapi.schemas.empi import WorkItemExtendedSchema
from ukrdc_fastapi.utils import daterange


def select_workitems(
    statuses: Optional[list[int]] = None,
    master_id: Optional[list[int]] = None,
    person_id: Optional[list[int]] = None,
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
) -> Select:
    """Get a list of WorkItems

    Args:
        statuses (list[int], optional): WorkItem statuses to filter by. Defaults to None.
        master_id (Optional[int], optional): WorkItem MasterRecord ID to filter by. Defaults to None.
        person_id (Optional[int], optional): WorkItem person ID to filter by. Defaults to None.
        facility (Optional[str], optional): Associated Person sending facility to filter by. Defaults to None.
        since (Optional[datetime.datetime], optional): Show items since datetime. Defaults to None.
        until (Optional[datetime.datetime], optional): Show items until datetime. Defaults to None.

    Returns:
        Select: SQLAlchemy query
    """
    status_list: list[int] = statuses or [1]

    stmt = select(WorkItem)

    if facility:
        stmt = (
            stmt.outerjoin(Person)
            .outerjoin(PidXRef)
            .where(
                or_(
                    PidXRef.sending_facility == facility,
                    WorkItem.attributes.like(f'%"SF":"{facility}"%'),
                )
            )
        )

    # Optionally filter Workitems updated since
    if since:
        stmt = stmt.where(WorkItem.last_updated >= since)

    # Optionally filter Workitems updated before
    if until:
        stmt = stmt.where(WorkItem.last_updated <= until)

    filters = []
    if master_id:
        filters.append(WorkItem.master_id.in_(master_id))
    if person_id:
        filters.append(WorkItem.person_id.in_(person_id))

    if master_id or person_id:
        stmt = stmt.where(or_(*filters))

    # Get a query of open workitems
    return stmt.where(WorkItem.status.in_(status_list))


def extend_workitem(workitem: WorkItem, jtrace: Session) -> WorkItemExtendedSchema:
    """Return a WorkItem by ID if it exists and the user has permission

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        workitem (WorkItem): WorkItem

    Returns:
        WorkItemExtendedSchema: Extended WorkItem object
    """
    # Expand incoming master records (if incoming person exists)
    if workitem.person:
        stmt = select_masterrecords_related_to_person(
            workitem.person, jtrace, nationalid_type="UKRDC"
        ).where(MasterRecord.id != workitem.master_id)

        master_records = jtrace.scalars(stmt).all()
    else:
        master_records = []

    incoming = {
        "person": workitem.person or None,
        "master_records": master_records,
    }

    # Expand destination persons (if destination master record exists)
    if workitem.master_record:
        stmt = select_persons_related_to_masterrecord(
            workitem.master_record, jtrace
        ).where(Person.id != workitem.person_id)
        persons = jtrace.scalars(stmt).all()
    else:
        persons = []

    destination = {
        "master_record": workitem.master_record or None,
        "persons": persons,
    }

    # Return extended workitem
    return WorkItemExtendedSchema(
        id=workitem.id,
        type=workitem.type,
        description=workitem.description,
        status=workitem.status,
        creation_date=workitem.creation_date,
        last_updated=workitem.last_updated,
        updated_by=workitem.updated_by,
        update_description=workitem.update_description,
        person=workitem.person,
        master_record=workitem.master_record,
        attributes=workitem.attributes,
        incoming=incoming,
        destination=destination,
    )


def select_workitem_collection(workitem: WorkItem, jtrace: Session) -> Select:
    """Get a list of WorkItems related via the LinkRecord network to a given WorkItem,
    raised by the same even as the given WorkItem.

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        workitem (WorkItem): WorkItem ID

    Returns:
        Select: SQLAlchemy query
    """
    stmt = select_workitems_related_to_workitem(workitem, jtrace)
    return stmt.where(WorkItem.creation_date == workitem.creation_date)


def select_workitems_related_to_workitem(workitem: WorkItem, jtrace: Session) -> Select:
    """Get a list of WorkItems related via the LinkRecord network to a given WorkItem

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        workitem (WorkItem): WorkItem ID

    Returns:
        Select: SQLAlchemy query
    """
    seen_master_ids: set[int] = set()
    seen_person_ids: set[int] = set()

    if workitem.master_record:
        seen_master_ids.add(workitem.master_id)
    if workitem.person:
        seen_person_ids.add(workitem.person_id)

    related_master_ids, related_person_ids = find_related_ids(
        jtrace, seen_master_ids, seen_person_ids
    )

    stmt = select(WorkItem).where(
        or_(
            WorkItem.master_id.in_(related_master_ids),
            WorkItem.person_id.in_(related_person_ids),
        )
    )

    return stmt.where(WorkItem.id != workitem.id)


def select_workitems_related_to_message(message: Message, jtrace: Session) -> Select:
    """Get a list of WorkItems related via the Patient Number to a given Message

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        message (Message): Message ID

    Returns:
        Select: SQLAlchemy query
    """
    # Get masterrecords directly referenced by the error
    stmt = select(MasterRecord).where(
        MasterRecord.nationalid == message.ni,
    )
    direct_records: list[MasterRecord] = jtrace.scalars(stmt).all()

    # Get workitems related to masterrecords directly referenced by the error
    return select(WorkItem).where(
        WorkItem.master_id.in_([record.id for record in direct_records]),
        WorkItem.status == 1,
    )


def get_full_workitem_history(
    jtrace: Session,
    since: Optional[datetime.date] = None,
    until: Optional[datetime.date] = None,
):
    """Get a combined workitem history by grouping and counting workitems by creation date.

    Args:
        jtrace (Session): SQLAlchemy session to the JTRACE database.
        since (Optional[datetime.date], optional): Start date. Defaults to last 365 days.
        until (Optional[datetime.date], optional): End date. Defaults to None.

    Returns:
        list[HistoryPoint]: Error history points.
    """

    # Get range
    range_since: datetime.date = since or datetime.date.today() - datetime.timedelta(
        days=365
    )
    range_until: datetime.date = until or datetime.date.today()

    # Get history within range
    trunc_func = func.date_trunc("day", WorkItem.creation_date)
    stmt_history = (
        select(trunc_func, func.count(trunc_func))
        .where(trunc_func >= range_since)
        .where(trunc_func <= range_until)
        .group_by(trunc_func)
        .order_by(trunc_func)
    )
    history = jtrace.execute(stmt_history)

    # Create an initially empty full history dictionary
    full_history: dict[datetime.date, int] = {
        date: 0 for date in daterange(range_since, range_until)
    }

    # For each non-zero history point, add it to the full history
    for history_point in history:
        full_history[history_point[0]] = history_point[-1]

    points = [
        HistoryPoint(time=date, count=count) for date, count in full_history.items()
    ]
    points.sort(key=lambda p: p.time)

    return points
