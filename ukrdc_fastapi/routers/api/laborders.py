import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import LabOrder, PVDelete

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.schemas.laborder import LabOrderSchema, LabOrderShortSchema
from ukrdc_fastapi.utils import filters
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


@router.get("/", response_model=Page[LabOrderShortSchema])
def laborders(ni: Optional[str] = None, ukrdc3: Session = Depends(get_ukrdc3)):
    """Retreive a list of all lab orders"""
    orders = ukrdc3.query(LabOrder)
    # Optionally filter by NI
    if ni:
        orders = filters.laborders_by_ni(ukrdc3, orders, ni)
    # Sort by collected time
    orders = orders.order_by(LabOrder.specimen_collected_time.desc())
    return paginate(orders)


@router.get("/{order_id}", response_model=LabOrderSchema)
def laborder_get(order_id: str, ukrdc3: Session = Depends(get_ukrdc3)):
    """Retreive a particular lab order"""
    order = ukrdc3.query(LabOrder).get(order_id)
    if not order:
        raise HTTPException(404, detail="Lab order not found")
    return order


@router.delete("/{order_id}", status_code=204)
def laborder_delete(order_id: str, ukrdc3: Session = Depends(get_ukrdc3)):
    """Mark a particular lab order for deletion"""
    order: LabOrder = ukrdc3.query(LabOrder).get(order_id)
    pid = order.pid
    deletes = [
        PVDelete(
            pid=pid,
            observation_time=item.observation_time,
            service_id=item.service_id,
        )
        for item in order.result_items
    ]
    ukrdc3.bulk_save_objects(deletes)

    for item in deletes:
        logging.info(
            "DELETING result item: %s - %s (%s)",
            item.pid,
            item.service_id,
            item.observation_time,
        )
    logging.info("DELETING lab order: %s - %s", order.id, order.pid)

    ukrdc3.delete(order)
    ukrdc3.commit()
