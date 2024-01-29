import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query as QueryParam
from fastapi import Security
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import LabOrder, PatientRecord, ResultItem

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.schemas.patientrecord.laborder import ResultItemSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import SQLASorter, make_sqla_sorter

from .dependencies import _get_patientrecord

router = APIRouter()


@router.get(
    "",
    response_model=Page[ResultItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_results(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    ukrdc3: Session = Depends(get_ukrdc3),
    service_id: Optional[list[str]] = QueryParam([]),
    order_id: Optional[list[str]] = QueryParam([]),
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    sorter: SQLASorter = Depends(
        make_sqla_sorter(
            [ResultItem.observation_time, ResultItem.entered_on],
            default_sort_by=ResultItem.observation_time,
        )
    ),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's lab orders"""
    stmt = select(ResultItem).where(ResultItem.pid == patient_record.pid)

    if service_id:
        stmt = stmt.where(ResultItem.service_id.in_(service_id))
    if order_id:
        stmt = stmt.where(ResultItem.order_id.in_(order_id))
    if since:
        stmt = stmt.where(ResultItem.observation_time >= since)
    if until:
        stmt = stmt.where(ResultItem.observation_time <= until)

    audit.add_event(
        Resource.RESULTITEMS,
        None,
        AuditOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.READ
        ),
    )

    return paginate(ukrdc3, sorter.sort(stmt))


@router.get(
    "/{resultitem_id}",
    response_model=ResultItemSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_result(
    resultitem_id: str,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    ukrdc3: Session = Depends(get_ukrdc3),
    audit: Auditer = Depends(get_auditer),
) -> ResultItem:
    """Retreive a particular lab result"""
    stmt = select(ResultItem).where(ResultItem.id == resultitem_id)
    item = ukrdc3.execute(stmt).scalar_one_or_none()

    if not item:
        raise HTTPException(404, detail="Result item not found")

    audit.add_event(
        Resource.RESULTITEM,
        resultitem_id,
        AuditOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.READ
        ),
    )

    return item


@router.delete(
    "/{resultitem_id}",
    dependencies=[Security(auth.permission(Permissions.WRITE_RECORDS))],
)
def patient_result_delete(
    resultitem_id: str,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    ukrdc3: Session = Depends(get_ukrdc3),
    audit: Auditer = Depends(get_auditer),
):
    """Mark a particular lab result for deletion"""
    stmt = select(ResultItem).where(ResultItem.id == resultitem_id)
    item = ukrdc3.execute(stmt).scalar_one_or_none()

    if not item:
        raise HTTPException(404, detail="Result item not found")

    order: Optional[LabOrder] = item.order

    ukrdc3.delete(item)
    ukrdc3.commit()

    # If the parent order has no more items, delete it too
    if order:
        stmt_other_items = select(ResultItem).where(ResultItem.order_id == order.id)
        first_item = ukrdc3.execute(stmt_other_items).scalar_one_or_none()
        if not first_item:
            ukrdc3.delete(order)
            ukrdc3.commit()

    audit.add_event(
        Resource.RESULTITEM,
        resultitem_id,
        AuditOperation.DELETE,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.UPDATE
        ),
    )

    return Response(status_code=204)
