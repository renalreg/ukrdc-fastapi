import pytest
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.query import messages

from ..utils import days_ago


def test_get_messages(
    errorsdb_session,
):
    all_msgs = messages.get_messages(errorsdb_session, since=days_ago(730))
    # Superuser should see all error messages
    assert {error.id for error in all_msgs} == {1, 2, 3}


def test_get_errors(errorsdb_session):
    all_msgs = messages.get_messages(
        errorsdb_session, statuses=["ERROR"], since=days_ago(730)
    )
    # Superuser should see all error messages
    assert {error.id for error in all_msgs} == {2, 3}


def test_get_errors_until(errorsdb_session):
    all_errors = messages.get_messages(
        errorsdb_session,
        since=days_ago(730),
        until=days_ago(3),
    )
    assert {error.id for error in all_errors} == {3}


def test_get_errors_facility(errorsdb_session):
    all_errors = messages.get_messages(
        errorsdb_session,
        since=days_ago(730),
        facility="TSF02",
    )
    assert {error.id for error in all_errors} == {3}


def test_get_errors_channel(errorsdb_session):
    all_errors = messages.get_messages(
        errorsdb_session,
        since=days_ago(730),
        channels=["00000000-0000-0000-0000-111111111111"],
    )
    assert {error.id for error in all_errors} == {2}


def test_get_errors_multiple_channels(errorsdb_session):
    all_errors = messages.get_messages(
        errorsdb_session,
        since=days_ago(730),
        channels=[
            "00000000-0000-0000-0000-000000000000",
            "00000000-0000-0000-0000-111111111111",
        ],
    )
    assert {error.id for error in all_errors} == {1, 2, 3}


def test_get_messages_nis(errorsdb_session):
    all_msgs = messages.get_messages(
        errorsdb_session, since=days_ago(730), nis=["999999999"]
    )
    assert {error.id for error in all_msgs} == {1, 2}


def test_get_masterrecord_messages(errorsdb_session, jtrace_session):
    error_list = messages.get_messages_related_to_masterrecord(
        jtrace_session.query(MasterRecord).get(1), errorsdb_session, jtrace_session
    ).all()
    assert {error.id for error in error_list} == {1, 2}


def test_get_masterrecord_errors(errorsdb_session, jtrace_session):
    error_list = messages.get_messages_related_to_masterrecord(
        jtrace_session.query(MasterRecord).get(1),
        errorsdb_session,
        jtrace_session,
        statuses=["ERROR"],
    ).all()
    assert {error.id for error in error_list} == {2}


@pytest.mark.asyncio
async def test_get_message_source(mirth_session, errorsdb_session, httpx_session):
    message = errorsdb_session.query(Message).get(1)
    source = await messages.get_message_source(message, mirth_session)
    assert (
        source.content
        == '<?xml version="1.0" encoding="UTF-8"?>\n            <testelement>\n            </testelement>'
    )
