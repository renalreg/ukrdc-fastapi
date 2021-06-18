import datetime

import pytest

from ukrdc_fastapi.query import workitems
from ukrdc_fastapi.query.common import PermissionsError


def test_get_workitems_superuser(jtrace_session, superuser):
    all_items = workitems.get_workitems(jtrace_session, superuser)
    assert {item.id for item in all_items} == {1, 2, 3}


def test_get_workitems_user(jtrace_session, test_user):
    all_items = workitems.get_workitems(jtrace_session, test_user)
    assert {item.id for item in all_items} == {2, 3}


def test_get_workitems_facility(jtrace_session, superuser):
    all_items = workitems.get_workitems(jtrace_session, superuser, statuses=[3])
    assert {item.id for item in all_items} == {4}


def test_get_workitems_statuses(jtrace_session, superuser):
    all_items = workitems.get_workitems(
        jtrace_session, superuser, facility="TEST_SENDING_FACILITY_1"
    )
    assert {item.id for item in all_items} == {2, 3}


def test_get_workitems_since(jtrace_session, superuser):
    all_items = workitems.get_workitems(
        jtrace_session, superuser, since=datetime.datetime(2021, 1, 1)
    )
    assert {item.id for item in all_items} == {2, 3}


def test_get_workitems_until(jtrace_session, superuser):
    all_items = workitems.get_workitems(
        jtrace_session, superuser, until=datetime.datetime(2020, 12, 1)
    )
    assert {item.id for item in all_items} == {1}


def test_get_workitems_masterid(jtrace_session, superuser):
    all_items = workitems.get_workitems(jtrace_session, superuser, master_id=[1])
    assert {item.id for item in all_items} == {1, 2}


def test_get_workitem_superuser(jtrace_session, superuser):
    record = workitems.get_workitem(jtrace_session, 1, superuser)
    assert record
    assert record.id == 1


def test_get_workitem_user(jtrace_session, test_user):
    record = workitems.get_workitem(jtrace_session, 2, test_user)
    assert record
    assert record.id == 2


def test_get_workitem_denied(jtrace_session, test_user):
    with pytest.raises(PermissionsError):
        workitems.get_workitem(jtrace_session, 1, test_user)


@pytest.mark.asyncio
async def test_update_workitem(
    jtrace_session, redis_session, mirth_session, superuser, httpx_session
):
    response = await workitems.update_workitem(
        jtrace_session,
        1,
        superuser,
        mirth_session,
        redis_session,
        status=3,
        comment="UPDATE COMMENT",
    )

    assert response.status == "success"
    message = response.message

    assert "<workitem>1</workitem>" in message
    assert "<status>3</status>" in message
    assert "<updateDescription>UPDATE COMMENT</updateDescription>" in message
    assert "<updatedBy>TEST@UKRDC_FASTAPI</updatedBy>" in message


def test_get_workitems_related(jtrace_session, superuser):
    all_items = workitems.get_workitems_related_to_workitem(
        jtrace_session, 1, superuser
    )
    assert {item.id for item in all_items} == {2}
