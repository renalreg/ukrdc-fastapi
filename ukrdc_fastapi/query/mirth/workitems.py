from typing import Optional

from mirth_client.mirth import MirthAPI
from redis import Redis
from ukrdc_sqla.empi import WorkItem

from ukrdc_fastapi.query.mirth.base import safe_send_mirth_message_to_name
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema
from ukrdc_fastapi.utils.mirth.messages import (
    build_close_workitem_message,
    build_update_workitem_message,
)


async def update_workitem(
    workitem: WorkItem,
    mirth: MirthAPI,
    redis: Redis,
    user_id: str,
    status: Optional[int] = None,
    comment: Optional[str] = None,
) -> MirthMessageResponseSchema:
    """Update a WorkItem by ID if it exists and the user has permission

    Args:
        workitem (WorkItem): WorkItem Object
        mirth (MirthAPI): Mirth API instance
        redis (Redis): Redis session
        user_id (str): User ID
        status (int, optional): New WorkItem status
        comment (str, optional): User comment to add to WorkItem

    Returns:
        MirthMessageResponseSchema: Mirth API response object
    """
    if not workitem.id:
        raise ValueError("WorkItem has no ID")  # pragma: no cover

    target_status: Optional[int] = status or workitem.status

    if not target_status:
        raise ValueError("WorkItem status is not valid")  # pragma: no cover

    return await safe_send_mirth_message_to_name(
        "WorkItemUpdate",
        build_update_workitem_message(
            workitem.id,
            target_status,
            comment or workitem.description,
            user_id,
        ),
        mirth,
        redis,
    )


async def close_workitem(
    workitem: WorkItem,
    mirth: MirthAPI,
    redis: Redis,
    user_id: str,
    comment: Optional[str] = None,
) -> MirthMessageResponseSchema:
    """Close a WorkItem by ID if it exists and the user has permission

    Args:
        workitem (WorkItem): WorkItem ID
        mirth (MirthAPI): Mirth API instance
        redis (Redis): Redis session
        user_id (str): User ID
        comment (str, optional): User comment to add to WorkItem

    Returns:
        MirthMessageResponseSchema: Mirth API response object
    """
    if not workitem.id:
        raise ValueError("WorkItem has no ID")  # pragma: no cover

    return await safe_send_mirth_message_to_name(
        "WorkItemUpdate",
        build_close_workitem_message(workitem.id, comment or "", user_id),
        mirth,
        redis,
    )
