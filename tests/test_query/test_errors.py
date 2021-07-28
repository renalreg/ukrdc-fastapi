from datetime import datetime

import pytest
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.query import messages
from ukrdc_fastapi.query.common import PermissionsError


def test_get_errors_superuser(errorsdb_session, superuser):
    all_errors = messages.get_messages(
        errorsdb_session, superuser, since=datetime(1970, 1, 1)
    )
    # Superuser should see all error messages
    assert {error.id for error in all_errors} == {1, 2}


def test_get_errors_user(errorsdb_session, test_user):
    all_errors = messages.get_messages(
        errorsdb_session, test_user, since=datetime(1970, 1, 1)
    )
    # Test user should see error messages from TEST_SENDING_FACILITY_1
    assert {error.id for error in all_errors} == {1}


def test_get_errors_until(errorsdb_session, superuser):
    all_errors = messages.get_messages(
        errorsdb_session,
        superuser,
        since=datetime(1970, 1, 1),
        until=datetime(2020, 12, 12),
    )
    assert {error.id for error in all_errors} == {2}


def test_get_errors_facility(errorsdb_session, superuser):
    all_errors = messages.get_messages(
        errorsdb_session,
        superuser,
        since=datetime(1970, 1, 1),
        facility="TEST_SENDING_FACILITY_2",
    )
    assert {error.id for error in all_errors} == {2}


def test_get_errors_nis(errorsdb_session, superuser):
    all_errors = messages.get_messages(
        errorsdb_session, superuser, since=datetime(1970, 1, 1), nis=["999999999"]
    )
    assert {error.id for error in all_errors} == {1}


def test_get_error_superuser(errorsdb_session, superuser):
    error = messages.get_message(errorsdb_session, 1, superuser)
    assert error
    assert error.id == 1


def test_get_error_user(errorsdb_session, test_user):
    error = messages.get_message(errorsdb_session, 1, test_user)
    assert error
    assert error.id == 1


def test_get_error_user_denied(errorsdb_session, test_user):
    with pytest.raises(PermissionsError):
        messages.get_message(errorsdb_session, 2, test_user)


def test_get_masterrecord_errors(errorsdb_session, jtrace_session, superuser):
    error_list = messages.get_messages_related_to_masterrecord(
        errorsdb_session, jtrace_session, 1, superuser
    ).all()
    assert {error.id for error in error_list} == {1}


def test_get_masterrecord_latest(errorsdb_session, jtrace_session, superuser):
    latest = messages.get_last_message_on_masterrecord(
        jtrace_session, errorsdb_session, 1, superuser
    )
    assert latest.id == 1

    # Create a new master record
    master_record_3 = MasterRecord(
        id=3,
        status=0,
        last_updated=datetime(2021, 1, 1),
        date_of_birth=datetime(1980, 12, 12),
        nationalid="119999999",
        nationalid_type="UKRDC",
        effective_date=datetime(2021, 1, 1),
    )

    # Person 3 now has 2 master records we want to merge
    jtrace_session.add(master_record_3)
    jtrace_session.commit()

    latest = messages.get_last_message_on_masterrecord(
        jtrace_session, errorsdb_session, 3, superuser
    )
    assert latest is None
