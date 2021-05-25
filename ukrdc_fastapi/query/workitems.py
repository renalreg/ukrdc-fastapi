import datetime
from typing import Optional

from fastapi.exceptions import HTTPException
from httpx import Response
from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import or_
from ukrdc_sqla.empi import Person, PidXRef, WorkItem

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.utils.mirth import (
    MirthMessageResponseSchema,
    build_update_workitem_message,
    get_channel_from_name,
)


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
    xref: PidXRef
    for xref in person.xref_entries:
        if xref.sending_facility in units:
            return

    raise HTTPException(
        403,
        detail="You do not have permission to access this resource. Sending facility does not match.",
    )


def get_workitems(
    jtrace: Session,
    user: UKRDCUser,
    statuses: list[int] = None,
    master_id: Optional[int] = None,
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
):
    status_list: list[int] = statuses or [1]

    workitems = jtrace.query(WorkItem)

    if facility:
        workitems = (
            workitems.join(Person)
            .join(PidXRef)
            .filter(PidXRef.sending_facility == facility)
        )

    # Optionally filter Workitems updated since
    if since:
        workitems = workitems.filter(WorkItem.last_updated >= since)

    # Optionally filter Workitems updated before
    if until:
        workitems = workitems.filter(WorkItem.last_updated <= until)

    if master_id:
        workitems = workitems.filter(WorkItem.master_id == master_id)

    # Get a query of open workitems
    workitems = workitems.filter(WorkItem.status.in_(status_list))

    # Sort workitems
    workitems = workitems.order_by(WorkItem.last_updated.desc())

    return _apply_query_permissions(workitems, user)


def get_workitem(jtrace: Session, workitem_id: int, user: UKRDCUser) -> WorkItem:
    """Return a WorkItem by ID if it exists and the user has permission

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        workitem_id (int): WorkItem ID
        user (UKRDCUser): User object

    Raises:
        HTTPException: User does not have permission to access the resource

    Returns:
        WorkItem: WorkItem
    """
    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")
    _assert_permission(workitem, user)
    return workitem


async def update_workitem(
    jtrace: Session,
    workitem_id: int,
    user: UKRDCUser,
    mirth: MirthAPI,
    redis: Redis,
    status: Optional[int] = None,
    comment: Optional[str] = None,
) -> MirthMessageResponseSchema:
    workitem = get_workitem(jtrace, workitem_id, user)

    channel = await get_channel_from_name("WorkItemUpdate", mirth, redis)

    if not channel:
        raise HTTPException(
            500, detail="ID for WorkItemUpdate channel not found"
        )  # pragma: no cover

    message: str = build_update_workitem_message(
        workitem.id,
        status or workitem.status,
        comment or workitem.description,
        user.email,
    )

    response: Response = await channel.post_message(message)

    if response.status_code != 204:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


def get_workitems_related_to_workitem(
    jtrace: Session, workitem_id: int, user: UKRDCUser
):
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
