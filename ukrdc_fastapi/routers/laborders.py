import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.models.ukrdc import LabOrder, PVDelete
from ukrdc_fastapi.schemas.laborder import LabOrderSchema

router = APIRouter()


def _inject_href(request: Request, laborder: LabOrder):
    laborder.href = request.url_for("laborder_get", order_id=laborder.id)


@router.get("/{order_id}", response_model=LabOrderSchema)
def laborder_get(self, order_id: str, ukrdc3: Session = Depends(get_ukrdc3)):
    laborder = ukrdc3.query(LabOrder).get(order_id)
    if not laborder:
        raise HTTPException(404, detail="Lab order not found")
    _inject_href(laborder)
    return laborder


@router.delete("/{order_id}", status_code=204)
def laborder_delete(self, order_id: str, ukrdc3: Session = Depends(get_ukrdc3)):
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
