import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.ukrdc import LabOrder, PVDelete

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.query.common import PermissionsError


def _apply_query_permissions(query: Query, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return query

    return query.filter(
        LabOrder.receiving_location.in_(units)
        | LabOrder.entered_at.in_(units)
        | LabOrder.entering_organization_code.in_(units)
    )


def _assert_permission(laborder: LabOrder, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return

    if not (
        laborder.receiving_location in units
        or laborder.entered_at in units
        or laborder.entering_organization_code in units
    ):
        raise PermissionsError()


def get_laborders(ukrdc3: Session, user: UKRDCUser, pid: Optional[str] = None):
    """Return a list of laborders

    Args:
        ukrdc3 (Session): SQLAlchemy session
        user (UKRDCUser): Logged-in user
        pid (Optional[str], optional): PatientRecord PID to filer by. Defaults to None.

    Returns:
        Query: SQLAlchemy query
    """
    orders = ukrdc3.query(LabOrder)

    if pid:
        orders = orders.filter(LabOrder.pid == pid)

    return _apply_query_permissions(orders, user)


def get_laborder(ukrdc3: Session, order_id: str, user: UKRDCUser) -> LabOrder:
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
    _assert_permission(order, user)
    return order


def delete_laborder(ukrdc3: Session, order_id: str, user: UKRDCUser) -> None:
    """Delete a LabOrder by ID if it exists and the user has permission

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        order_id (str): LabOrder ID
        user (UKRDCUser): User object
    """
    order: LabOrder = get_laborder(ukrdc3, order_id, user)

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
