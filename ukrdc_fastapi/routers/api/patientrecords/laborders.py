from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import (
    LabOrder,
    PatientRecord,
    PVDelete,
)

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.schemas.laborder import (
    LabOrderSchema,
    LabOrderShortSchema,
)
from ukrdc_fastapi.utils.paginate import Page, paginate

from .dependencies import _get_patientrecord

router = APIRouter()


@router.get(
    "",
    response_model=Page[LabOrderShortSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_laborders(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's lab orders"""
    audit.add_event(
        Resource.LABORDERS,
        None,
        AuditOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.READ
        ),
    )

    return paginate(
        patient_record.lab_orders.order_by(LabOrder.specimen_collected_time.desc())
    )


@router.get(
    "/{order_id}",
    response_model=LabOrderSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_laborder(
    order_id: str,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
) -> LabOrder:
    """Retreive a particular lab order"""
    order = patient_record.lab_orders.filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, detail="Lab Order not found")

    audit.add_event(
        Resource.LABORDER,
        order_id,
        AuditOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.READ
        ),
    )

    return order


@router.delete(
    "/{order_id}",
    dependencies=[Security(auth.permission(Permissions.WRITE_RECORDS))],
)
def patient_laborder_delete(
    order_id: str,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    ukrdc3: Session = Depends(get_ukrdc3),
    audit: Auditer = Depends(get_auditer),
):
    """Mark a particular lab order for deletion"""
    order = patient_record.lab_orders.filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, detail="Lab Order not found")

    deletes = [
        PVDelete(
            pid=item.pid,
            observationtime=item.observation_time,
            serviceidcode=item.service_id,
        )
        for item in order.result_items
    ]

    # Audit the laborder delete and then each resulitem delete
    order_audit = audit.add_event(
        Resource.LABORDER,
        order_id,
        AuditOperation.DELETE,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.UPDATE
        ),
    )
    for item in order.result_items:
        audit.add_event(
            Resource.RESULTITEM,
            item.id,
            AuditOperation.DELETE,
            parent=order_audit,
        )

    ukrdc3.bulk_save_objects(deletes)
    ukrdc3.delete(order)
    ukrdc3.commit()

    return Response(status_code=204)
