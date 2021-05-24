import logging

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import LabOrder, PVDelete

from ukrdc_fastapi.access_models.ukrdc import LabOrderAM
from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.schemas.laborder import LabOrderSchema, LabOrderShortSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter(tags=["Lab Orders"])


def safe_get_laborder(ukrdc3: Session, order_id: str, user: UKRDCUser) -> LabOrder:
    """Return a LabOrder by ID if it exists and the user has permission

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        order_id (str): LabOrder ID
        user (UKRDCUser): User object

    Raises:
        HTTPException: User does not have permission to access the resource

    Returns:
        LabOrder: LabOrder
    """
    order = ukrdc3.query(LabOrder).get(order_id)
    if not order:
        raise HTTPException(404, detail="Lab order not found")
    LabOrderAM.assert_permission(order, user)
    return order


@router.get(
    "/",
    response_model=Page[LabOrderShortSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def laborders(
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of all lab orders"""
    orders = ukrdc3.query(LabOrder)
    # Sort by collected time
    orders = orders.order_by(LabOrder.specimen_collected_time.desc())

    orders = LabOrderAM.apply_query_permissions(orders, user)
    return paginate(orders)


@router.get(
    "/{order_id}/",
    response_model=LabOrderSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def laborder_get(
    order_id: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a particular lab order"""
    order: LabOrder = safe_get_laborder(ukrdc3, order_id, user)
    return order


@router.delete(
    "/{order_id}/",
    status_code=204,
    dependencies=[Security(auth.permission(Permissions.WRITE_RECORDS))],
)
def laborder_delete(
    order_id: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Mark a particular lab order for deletion"""
    order: LabOrder = safe_get_laborder(ukrdc3, order_id, user)

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
