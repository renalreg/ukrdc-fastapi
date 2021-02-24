import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.models.ukrdc import LabOrder, PVDelete
from ukrdc_fastapi.schemas.laborder import LabOrderSchema, LabOrderShortSchema
from ukrdc_fastapi.utils import filters

router = APIRouter()


@router.get("/", response_model=Page[LabOrderShortSchema])
def laborders(ni: Optional[str] = None, ukrdc3: Session = Depends(get_ukrdc3)):
    laborders = ukrdc3.query(LabOrder)
    # Optionally filter by NI
    if ni:
        laborders = filters.laborders_by_ni(ukrdc3, laborders, ni)
    # Sort by collected time
    laborders = laborders.order_by(LabOrder.specimen_collected_time.desc())
    return paginate(laborders)


@router.get("/{order_id}", response_model=LabOrderSchema)
def laborder_get(order_id: str, ukrdc3: Session = Depends(get_ukrdc3)):
    laborder = ukrdc3.query(LabOrder).get(order_id)
    if not laborder:
        raise HTTPException(404, detail="Lab order not found")
    return laborder


@router.delete("/{order_id}", status_code=204)
def laborder_delete(order_id: str, ukrdc3: Session = Depends(get_ukrdc3)):
    laborder: LabOrder = ukrdc3.query(LabOrder).get(order_id)
    pid = laborder.pid
    deletes = [
        PVDelete(
            pid=pid,
            observation_time=item.observation_time,
            service_id=item.service_id,
        )
        for item in laborder.result_items
    ]
    ukrdc3.bulk_save_objects(deletes)

    for item in deletes:
        logging.info(
            "DELETING result item: %s - %s (%s)",
            item.pid,
            item.service_id,
            item.observation_time,
        )
    logging.info("DELETING lab order: %s - %s", laborder.id, laborder.pid)

    ukrdc3.delete(laborder)
    ukrdc3.commit()
