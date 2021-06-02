import datetime

import pytest
from ukrdc_sqla.ukrdc import LabOrder, ResultItem

from ukrdc_fastapi.query import resultitems
from ukrdc_fastapi.query.common import PermissionsError


def test_get_resultitems_superuser(ukrdc3_session, superuser):
    all_items = resultitems.get_resultitems(ukrdc3_session, superuser)
    # Superuser should see all items
    assert {order.id for order in all_items} == {"RESULTITEM1", "RESULTITEM2"}


def test_get_resultitems_user(ukrdc3_session, test_user):
    all_items = resultitems.get_resultitems(ukrdc3_session, test_user)
    # Test user should see items from TEST_SENDING_FACILITY_1
    assert {order.id for order in all_items} == {"RESULTITEM1"}


def test_get_resultitems_pid(ukrdc3_session, superuser):
    all_items = resultitems.get_resultitems(
        ukrdc3_session, superuser, pid="PYTEST01:PV:00000000A"
    )
    assert {order.id for order in all_items} == {"RESULTITEM1", "RESULTITEM2"}

    all_items = resultitems.get_resultitems(
        ukrdc3_session, superuser, pid="MADE_UP_PID"
    )
    assert len(all_items.all()) == 0


def test_get_resultitems_service(ukrdc3_session, superuser):
    all_items = resultitems.get_resultitems(
        ukrdc3_session, superuser, service_id=["SERVICE_ID_1"]
    )
    assert {order.id for order in all_items} == {"RESULTITEM1"}


def test_get_resultitems_since(ukrdc3_session, superuser):
    all_items = resultitems.get_resultitems(
        ukrdc3_session, superuser, since=datetime.datetime(2021, 1, 1)
    )
    assert {item.id for item in all_items} == {"RESULTITEM2"}


def test_get_resultitems_until(ukrdc3_session, superuser):
    all_items = resultitems.get_resultitems(
        ukrdc3_session, superuser, until=datetime.datetime(2020, 12, 1)
    )
    assert {item.id for item in all_items} == {"RESULTITEM1"}


def test_get_resultitems_order(ukrdc3_session, superuser):
    all_items = resultitems.get_resultitems(
        ukrdc3_session, superuser, order_id=["LABORDER1"]
    )
    assert {order.id for order in all_items} == {"RESULTITEM1"}


def test_get_resultitem_services(ukrdc3_session, superuser):
    all_services = resultitems.get_resultitem_services(ukrdc3_session, superuser)
    assert {service.id for service in all_services} == {"SERVICE_ID_1", "SERVICE_ID_2"}


def test_get_resultitem_superuser(ukrdc3_session, superuser):
    order = resultitems.get_resultitem(ukrdc3_session, "RESULTITEM1", superuser)
    assert order
    assert order.id == "RESULTITEM1"


def test_get_resultitem_denied(ukrdc3_session, test_user):
    with pytest.raises(PermissionsError):
        resultitems.get_resultitem(ukrdc3_session, "RESULTITEM2", test_user)


def test_resultitem_delete(ukrdc3_session, superuser):
    # Delete the lab order
    resultitems.delete_resultitem(ukrdc3_session, "RESULTITEM2", superuser)

    # Make sure the lab order was deleted
    assert not ukrdc3_session.query(LabOrder).get("LABORDER2")
    assert not ukrdc3_session.query(ResultItem).get("RESULTITEM2")


def test_resultitem_delete_denied(ukrdc3_session, test_user):
    # Delete the lab order
    with pytest.raises(PermissionsError):
        resultitems.delete_resultitem(ukrdc3_session, "RESULTITEM2", test_user)
