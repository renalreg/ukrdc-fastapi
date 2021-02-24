from typing import List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.models.empi import MasterRecord, WorkItem
from ukrdc_fastapi.schemas.empi import WorkItemSchema, WorkItemShortSchema
from ukrdc_fastapi.utils import filter, post_mirth_message_and_catch
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()

MERGE_TEMPLATE = """<request>
    <superceding>{superceding}</superceding>
    <superceeded>{superceeded}</superceeded>
</request>
"""

UPDATE_WORKITEM_TEMPLATE = """<request>
    <workitem>{workitem}</workitem>
    <status>{status}</status>
    <updateDescription>{description}</updateDescription>
    <updatedBy>{user}</updatedBy>
</request>
"""

UNLINK_TEMPLATE = """<request>
    <masterRecord>{masterrecord}</masterRecord >
    <personId>{personid}</personId>
    <updateDescription>{description}</updateDescription>
    <updatedBy>{user}</updatedBy>
</request>
"""


class UnlinkWorkItemRequestSchema(BaseModel):
    master_record: str = Field(..., title="Master record ID")
    person_id: str = Field(..., title="Person ID")
    comment: Optional[str]
    mirth: Optional[bool] = Field(
        True,
        title="Post to Mirth",
        description="Disables sending the message to Mirth. Used for offline testing.",
    )


class CloseWorkItemRequestSchema(BaseModel):
    comment: Optional[str]
    mirth: Optional[bool] = Field(
        True,
        title="Post to Mirth",
        description="Disables sending the message to Mirth. Used for offline testing.",
    )


class MergeWorkItemRequestSchema(BaseModel):
    mirth: Optional[bool] = Field(
        True,
        title="Post to Mirth",
        description="Disables sending the message to Mirth. Used for offline testing.",
    )


class MirthMessageResponseSchema(BaseModel):
    """Response schema for Mirth message post views"""

    status: str
    message: str


@router.get("/", response_model=Page[WorkItemShortSchema])
def workitems_list(
    ukrdcid: Optional[List[str]] = Query(None),
    jtrace: Session = Depends(get_jtrace),
):
    # Get a query of open workitems
    query = jtrace.query(WorkItem).filter(WorkItem.status == 1)

    # If a list of UKRDCIDs is found in the query, filter by UKRDCIDs
    if ukrdcid:
        query = filter.workitems_by_ukrdcids(jtrace, query, ukrdcid)

    # Sort, paginate, and return
    return paginate(query.order_by(WorkItem.id))


@router.get("/{workitem_id}", response_model=WorkItemSchema)
def workitem_detail(
    workitem_id: int,
    jtrace: Session = Depends(get_jtrace),
):

    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    other_workitems = jtrace.query(WorkItem).filter(
        WorkItem.master_id == workitem.master_id,
        WorkItem.id != workitem.id,
        WorkItem.status == 1,
    )

    # Inject related workitems
    workitem.related = other_workitems.all()
    return workitem


@router.post("/{workitem_id}/close", response_model=MirthMessageResponseSchema)
def workitem_close(
    workitem_id: int,
    args: CloseWorkItemRequestSchema,
    jtrace: Session = Depends(get_jtrace),
):

    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    # Create and send the Mirth message
    message = UPDATE_WORKITEM_TEMPLATE.format(
        workitem=workitem.id,
        status=3,
        description=args.comment or "",
        user="UKRDC-API-v2-TESTING",  # TODO: Add user details when authenticated
    )

    return post_mirth_message_and_catch("workitem-update", message.strip(), args.mirth)


@router.post("/{workitem_id}/merge", response_model=MirthMessageResponseSchema)
def workitem_merge(
    workitem_id: int,
    args: MergeWorkItemRequestSchema,
    jtrace: Session = Depends(get_jtrace),
):

    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    # Get a set of related link record (id, person_id, master_id) tuples
    related_person_master_links: Set[
        filter.PersonMasterLink
    ] = filter.find_related_link_records(
        jtrace, workitem.master_id, person_id=workitem.person_id
    )

    # Find all related master records within the UKRDC
    master_with_ukrdc = (
        jtrace.query(MasterRecord)
        .filter(
            MasterRecord.id.in_(
                [link.master_id for link in related_person_master_links]
            )
        )
        .filter(MasterRecord.nationalid_type == "UKRDC")
        .order_by(MasterRecord.id)
        .all()
    )

    # If we don't have 2 records, something has gone wrong
    if len(master_with_ukrdc) != 2:
        raise HTTPException(
            400,
            detail=f"Got {len(master_with_ukrdc)} master record(s) with different UKRDC IDs. Expected 2.",
        )

    # Create and send the Mirth message
    message = MERGE_TEMPLATE.format(
        superceding=master_with_ukrdc[0].id, superceeded=master_with_ukrdc[1].id
    )

    return post_mirth_message_and_catch("merge", message.strip(), args.mirth)


@router.post("/unlink", response_model=MirthMessageResponseSchema)
def workitems_unlink(
    args: UnlinkWorkItemRequestSchema,
):

    message = UNLINK_TEMPLATE.format(
        masterrecord=args.master_record,
        personid=args.person_id,
        description=args.comment or "",
        user="UKRDC-API-v2-TESTING",  # TODO: Add user details when authenticated
    )

    return post_mirth_message_and_catch("unlink", message.strip(), args.mirth)
