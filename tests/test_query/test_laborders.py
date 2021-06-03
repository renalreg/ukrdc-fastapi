from datetime import datetime

import pytest
from ukrdc_sqla.ukrdc import LabOrder, ResultItem

from ukrdc_fastapi.query import laborders
from ukrdc_fastapi.query.common import PermissionsError


def test_get_laborders_superuser(ukrdc3_session, superuser):
    all_orders = laborders.get_laborders(ukrdc3_session, superuser)
    # Superuser should see all orders
    assert {order.id for order in all_orders} == {"LABORDER1", "LABORDER2"}


def test_get_laborders_user(ukrdc3_session, test_user):
    all_orders = laborders.get_laborders(ukrdc3_session, test_user)
    # Test user should see orders from TEST_SENDING_FACILITY_1
    assert {order.id for order in all_orders} == {"LABORDER1"}


def test_get_laborders_pid(ukrdc3_session, superuser):
    all_orders = laborders.get_laborders(
        ukrdc3_session, superuser, pid="PYTEST01:PV:00000000A"
    )
    assert {order.id for order in all_orders} == {"LABORDER1", "LABORDER2"}

    all_orders = laborders.get_laborders(ukrdc3_session, superuser, pid="MADE_UP_PID")
    assert len(all_orders.all()) == 0


def test_get_laborder_superuser(ukrdc3_session, superuser):
    order = laborders.get_laborder(ukrdc3_session, "LABORDER1", superuser)
    assert order
    assert order.id == "LABORDER1"


def test_get_laborder_denied(ukrdc3_session, test_user):
    with pytest.raises(PermissionsError):
        laborders.get_laborder(ukrdc3_session, "LABORDER2", test_user)


def test_laborder_delete(ukrdc3_session, superuser):
    # Delete the lab order
    laborders.delete_laborder(ukrdc3_session, "LABORDER2", superuser)

    # Make sure the lab order was deleted
    assert not ukrdc3_session.query(LabOrder).get("LABORDER2")
    assert not ukrdc3_session.query(ResultItem).get("RESULTITEM2")


def test_laborder_delete_denied(ukrdc3_session, test_user):
    # Delete the lab order
    with pytest.raises(PermissionsError):
        laborders.delete_laborder(ukrdc3_session, "LABORDER2", test_user)
