import datetime
from typing import Optional

from fastapi.exceptions import HTTPException
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import or_
from ukrdc_sqla.empi import MasterRecord, Person, PidXRef, WorkItem

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.query.common import PermissionsError, person_belongs_to_units
from ukrdc_fastapi.query.messages import get_message


def _apply_query_permissions(query: Query, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return query

    return query.join(Person).join(PidXRef).filter(PidXRef.sending_facility.in_(units))


def _assert_permission(workitem: WorkItem, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return

    person: Person = workitem.person
    if person_belongs_to_units(person, units):
        return

    raise PermissionsError()


def get_workitems(
    jtrace: Session,
    user: UKRDCUser,
    statuses: list[int] = None,
    master_id: Optional[list[int]] = None,
    person_id: Optional[list[int]] = None,
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
):
    """Get a list of WorkItems

    Args:
        jtrace (Session): SQLAlchemy session
        user (UKRDCUser): Logged-in user
        statuses (list[int], optional): WorkItem statuses to filter by. Defaults to None.
        master_id (Optional[int], optional): WorkItem MasterRecord ID to filter by. Defaults to None.
        facility (Optional[str], optional): Associated Person sending facility to filter by. Defaults to None.
        since (Optional[datetime.datetime], optional): Show items since datetime. Defaults to None.
        until (Optional[datetime.datetime], optional): Show items until datetime. Defaults to None.

    Returns:
        [type]: [description]
    """
    status_list: list[int] = statuses or [1]

    workitems = jtrace.query(WorkItem)

    if facility:
        workitems = (
            workitems.outerjoin(Person)
            .outerjoin(PidXRef)
            .filter(
                or_(
                    PidXRef.sending_facility == facility,
                    WorkItem.attributes.like(f'%"SF":"{facility}"%'),
                )
            )
        )

    # Optionally filter Workitems updated since
    if since:
        workitems = workitems.filter(WorkItem.last_updated >= since)

    # Optionally filter Workitems updated before
    if until:
        workitems = workitems.filter(WorkItem.last_updated <= until)

    filters = []
    if master_id:
        filters.append(WorkItem.master_id.in_(master_id))
    if person_id:
        filters.append(WorkItem.person_id.in_(person_id))

    if master_id or person_id:
        workitems = workitems.filter(or_(*filters))

    # Get a query of open workitems
    workitems = workitems.filter(WorkItem.status.in_(status_list))

    return _apply_query_permissions(workitems, user)


def get_workitem(jtrace: Session, workitem_id: int, user: UKRDCUser) -> WorkItem:
    """Return a WorkItem by ID if it exists and the user has permission

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        workitem_id (int): WorkItem ID
        user (UKRDCUser): User object

    Returns:
        WorkItem: WorkItem
    """
    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")
    _assert_permission(workitem, user)
    return workitem


def get_workitems_related_to_workitem(
    jtrace: Session, workitem_id: int, user: UKRDCUser
) -> Query:
    """Get a list of WorkItems related via the LinkRecord network to a given WorkItem

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        workitem_id (int): WorkItem ID
        user (UKRDCUser): Logged-in user

    Returns:
        Query: SQLAlchemy query
    """
    workitem = get_workitem(jtrace, workitem_id, user)

    filters = []
    if workitem.master_record:
        filters.append(WorkItem.master_id == workitem.master_id)
    if workitem.person:
        filters.append(WorkItem.person_id == workitem.person_id)

    other_workitems = jtrace.query(WorkItem).filter(
        or_(*filters),
        WorkItem.id != workitem.id,
        WorkItem.status == 1,
    )

    return _apply_query_permissions(other_workitems, user)


def get_workitems_related_to_message(
    jtrace: Session, errorsdb: Session, message_id: str, user: UKRDCUser
) -> Query:
    """Get a list of WorkItems related via the Patient Number to a given Message

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        errorsdb (Session): ERRORSDB SQLAlchemy session
        message_id (str): Message ID
        user (UKRDCUser): Logged-in user

    Returns:
        Query: SQLAlchemy query
    """
    error = get_message(errorsdb, message_id, user)

    # Get masterrecords directly referenced by the error
    direct_records: list[MasterRecord] = (
        jtrace.query(MasterRecord).filter(MasterRecord.nationalid == error.ni).all()
    )

    # Get workitems related to masterrecords directly referenced by the error
    return jtrace.query(WorkItem).filter(
        WorkItem.master_id.in_([record.id for record in direct_records]),
        WorkItem.status == 1,
    )
