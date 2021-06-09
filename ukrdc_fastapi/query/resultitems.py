import datetime
import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Query, Session
from ukrdc_sqla.ukrdc import LabOrder, ResultItem

from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.query.laborders import (
    _apply_query_permissions as _apply_laborder_query_permissions,
)
from ukrdc_fastapi.query.laborders import (
    _assert_permission as _assert_laborder_permission,
)
from ukrdc_fastapi.schemas.laborder import ResultItemServiceSchema


def _apply_query_permissions(query: Query, user: UKRDCUser):
    return _apply_laborder_query_permissions(query, user)


def _assert_permission(result: ResultItem, user: UKRDCUser):
    laborder: LabOrder = result.order
    return _assert_laborder_permission(laborder, user)


def get_resultitems(
    ukrdc3: Session,
    user: UKRDCUser,
    pid: Optional[str] = None,
    service_id: Optional[list[str]] = None,
    order_id: Optional[list[str]] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    sort_query: bool = True,
) -> Query:
    """Retreive a list of lab results, optionally filtered by NI or service ID

    Args:
        ukrdc3 (Session): SQLALchemy session
        user (UKRDCUser): Logged-in user
        pid (Optional[str], optional): PatientRecord PID to filer by. Defaults to None.
        service_id (Optional[list[str]], optional): Result services to filter by. Defaults to None.
        order_id (Optional[list[str]], optional): LabOrder ID to filer by. Defaults to None.
        since (Optional[datetime.datetime], optional): Show results since datetime. Defaults to None.
        until (Optional[datetime.datetime], optional): Show results until datetime. Defaults to None.

    Returns:
        Query: SQLAlchemy query
    """
    query: Query = ukrdc3.query(ResultItem).join(LabOrder.result_items)

    if pid:
        query = query.filter(LabOrder.pid == pid)
    if service_id:
        query = query.filter(ResultItem.service_id.in_(service_id))
    if order_id:
        query = query.filter(ResultItem.order_id.in_(order_id))
    if since:
        query = query.filter(ResultItem.observation_time >= since)
    if until:
        query = query.filter(ResultItem.observation_time <= until)

    if sort_query:
        query = query.order_by(ResultItem.entered_on.desc())

    return _apply_query_permissions(query, user)


def get_resultitem_services(
    ukrdc3: Session,
    user: UKRDCUser,
    pid: Optional[str] = None,
) -> list[ResultItemServiceSchema]:
    """Get a list of available result services

    Args:
        ukrdc3 (Session): SQLALchemy session
        user (UKRDCUser): Logged-in user object
        pid (Optional[str], optional): PID of resultiutem patientrecord. Defaults to None.

    Returns:
        list[ResultItemServiceSchema]: List of unique resultitem services
    """
    items = get_resultitems(ukrdc3, user, pid, sort_query=False)
    services = items.distinct(ResultItem.service_id)
    return [
        ResultItemServiceSchema(
            id=item.service_id,
            description=item.service_id_description,
            standard=item.service_id_std,
        )
        for item in services.all()
    ]


def get_resultitem(ukrdc3: Session, resultitem_id: str, user: UKRDCUser) -> ResultItem:
    """Return a ResultItem by ID if it exists and the user has permission

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        resultitem_id (str): ResultItem ID
        user (UKRDCUser): Logged-in user

    Returns:
        ResultItem: ResultItem
    """
    item: Optional[ResultItem] = ukrdc3.query(ResultItem).get(resultitem_id)
    if not item:
        raise HTTPException(404, detail="Result item not found")
    _assert_permission(item, user)
    return item


def delete_resultitem(ukrdc3: Session, resultitem_id: str, user: UKRDCUser) -> None:
    """Delete a ResultItem by ID if it exists and the user has permission

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        resultitem_id (str): ResultItem ID
        user (UKRDCUser): Logged-in user
    """
    item: Optional[ResultItem] = get_resultitem(ukrdc3, resultitem_id, user)

    if not item:
        raise HTTPException(404, detail="Result item not found")

    logging.info(
        "DELETING: %s %s (%s) - %s%s",
        item.order_id,
        item.service_id,
        item.observation_time,
        item.value,
        item.value_units if item.value_units else "",
    )
    ukrdc3.delete(item)
    ukrdc3.commit()

    order_id: Optional[str] = item.order_id
    if order_id:
        order: Optional[LabOrder] = ukrdc3.query(LabOrder).get(order_id)
        if order and order.result_items.count() == 0:
            logging.info(
                "DELETING laborder without any result items: %s %s",
                order.specimen_collected_time,
                order.entered_at,
            )

            ukrdc3.delete(order)
    ukrdc3.commit()
