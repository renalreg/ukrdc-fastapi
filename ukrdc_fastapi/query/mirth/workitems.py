from typing import Optional

from fastapi.exceptions import HTTPException
from mirth_client.exceptions import MirthPostError
from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm.session import Session

from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.exceptions import MirthChannelError
from ukrdc_fastapi.query.workitems import get_workitem
from ukrdc_fastapi.utils.mirth import (
    MirthMessageResponseSchema,
    build_close_workitem_message,
    build_update_workitem_message,
    get_channel_from_name,
)


async def update_workitem(
    jtrace: Session,
    workitem_id: int,
    user: UKRDCUser,
    mirth: MirthAPI,
    redis: Redis,
    status: Optional[int] = None,
    comment: Optional[str] = None,
) -> MirthMessageResponseSchema:
    """Update a WorkItem by ID if it exists and the user has permission

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        workitem_id (int): WorkItem ID
        user (UKRDCUser): User object
        mirth (MirthAPI): Mirth API instance
        redis (Redis): Redis session
        status (int, optional): New WorkItem status
        comment (str, optional): User comment to add to WorkItem

    Returns:
        MirthMessageResponseSchema: Mirth API response object
    """
    workitem = get_workitem(jtrace, workitem_id, user)

    channel = get_channel_from_name("WorkItemUpdate", mirth, redis)

    if not channel:
        raise MirthChannelError(
            "ID for WorkItemUpdate channel not found"
        )  # pragma: no cover

    message: str = build_update_workitem_message(
        workitem.id,
        status or workitem.status,
        comment or workitem.description,
        user.email,
    )
    try:
        await channel.post_message(message)
    except MirthPostError as e:
        raise HTTPException(500, str(e)) from e  # pragma: no cover

    return MirthMessageResponseSchema(status="success", message=message)


async def close_workitem(
    jtrace: Session,
    workitem_id: int,
    user: UKRDCUser,
    mirth: MirthAPI,
    redis: Redis,
    comment: Optional[str] = None,
) -> MirthMessageResponseSchema:
    """Close a WorkItem by ID if it exists and the user has permission

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        workitem_id (int): WorkItem ID
        user (UKRDCUser): User object
        mirth (MirthAPI): Mirth API instance
        redis (Redis): Redis session
        comment (str, optional): User comment to add to WorkItem

    Returns:
        MirthMessageResponseSchema: Mirth API response object
    """
    workitem = get_workitem(jtrace, workitem_id, user)

    channel = get_channel_from_name("WorkItemUpdate", mirth, redis)
    if not channel:
        raise MirthChannelError(
            "ID for WorkItemUpdate channel not found"
        )  # pragma: no cover

    message: str = build_close_workitem_message(workitem.id, comment or "", user.email)
    try:
        await channel.post_message(message)
    except MirthPostError as e:
        raise HTTPException(500, str(e)) from e  # pragma: no cover

    return MirthMessageResponseSchema(status="success", message=message)
