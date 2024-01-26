import pytest
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.ukrdc import PatientRecord

from tests.conftest import NI_1, PID_1
from ukrdc_fastapi.query import messages

from ..utils import days_ago


def test_get_messages(
    errorsdb_session,
):
    all_msgs = errorsdb_session.scalars(messages.select_messages(since=days_ago(730))).all()
    # Superuser should see all error messages
    assert {error.id for error in all_msgs} == {1, 2, 3}


def test_get_errors(errorsdb_session):
    all_msgs = errorsdb_session.scalars(messages.select_messages(
        statuses=["ERROR"], since=days_ago(730)
    )).all()
    # Superuser should see all error messages
    assert {error.id for error in all_msgs} == {2, 3}


def test_get_errors_until(errorsdb_session):
    all_errors = errorsdb_session.scalars(messages.select_messages(
        since=days_ago(730),
        until=days_ago(3),
    )).all()
    assert {error.id for error in all_errors} == {3}


def test_get_errors_facility(errorsdb_session):
    all_errors = errorsdb_session.scalars(messages.select_messages(
        since=days_ago(730),
        facility="TSF02",
    )).all()
    assert {error.id for error in all_errors} == {3}


def test_get_errors_channel(errorsdb_session):
    all_errors = errorsdb_session.scalars(messages.select_messages(
        since=days_ago(730),
        channels=["00000000-0000-0000-0000-111111111111"],
    )).all()
    assert {error.id for error in all_errors} == {2}


def test_get_errors_multiple_channels(errorsdb_session):
    all_errors = errorsdb_session.scalars(messages.select_messages(
        since=days_ago(730),
        channels=[
            "00000000-0000-0000-0000-000000000000",
            "00000000-0000-0000-0000-111111111111",
        ],
    )).all()
    assert {error.id for error in all_errors} == {1, 2, 3}


def test_get_messages_nis(errorsdb_session):
    all_msgs = errorsdb_session.scalars(messages.select_messages(since=days_ago(730), nis=[NI_1])).all()
    assert {error.id for error in all_msgs} == {1, 2}


def test_get_masterrecord_messages(errorsdb_session, jtrace_session):
    error_list = errorsdb_session.scalars(messages.select_messages_related_to_masterrecord(
        jtrace_session.get(MasterRecord, 1), jtrace_session
    )).all()
    assert {error.id for error in error_list} == {1, 2}


def test_get_masterrecord_errors(errorsdb_session, jtrace_session):
    error_list = errorsdb_session.scalars(messages.select_messages_related_to_masterrecord(
        jtrace_session.get(MasterRecord, 1),
        jtrace_session,
        statuses=["ERROR"],
    )).all()
    assert {error.id for error in error_list} == {2}


def test_get_patientrecord_messages(errorsdb_session, ukrdc3_session):
    error_list = errorsdb_session.scalars(messages.select_messages_related_to_patientrecord(
        ukrdc3_session.get(PatientRecord, PID_1)
    )).all()
    assert {error.id for error in error_list} == {1, 2}


def test_get_patientrecord_errors(errorsdb_session, ukrdc3_session):
    error_list = errorsdb_session.scalars(messages.select_messages_related_to_patientrecord(
        ukrdc3_session.get(PatientRecord, PID_1),
        statuses=["ERROR"],
    )).all()
    assert {error.id for error in error_list} == {2}


@pytest.mark.asyncio
async def test_get_message_source(mirth_session, errorsdb_session, httpx_session):
    message = errorsdb_session.get(Message, 1)
    source = await messages.get_message_source(message, mirth_session)
    assert (
        source.content
        == '<?xml version="1.0" encoding="UTF-8"?>\n            <testelement>\n            </testelement>'
    )
