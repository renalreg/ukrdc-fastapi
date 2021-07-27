from datetime import datetime

import pytest

from ukrdc_fastapi.query import errors
from ukrdc_fastapi.query.common import PermissionsError


def test_get_errors_superuser(errorsdb_session, superuser):
    all_errors = errors.get_errors(
        errorsdb_session, superuser, since=datetime(1970, 1, 1)
    )
    # Superuser should see all error messages
    assert {error.id for error in all_errors} == {1, 2}


def test_get_errors_user(errorsdb_session, test_user):
    all_errors = errors.get_errors(
        errorsdb_session, test_user, since=datetime(1970, 1, 1)
    )
    # Test user should see error messages from TEST_SENDING_FACILITY_1
    assert {error.id for error in all_errors} == {1}


def test_get_errors_until(errorsdb_session, superuser):
    all_errors = errors.get_errors(
        errorsdb_session,
        superuser,
        since=datetime(1970, 1, 1),
        until=datetime(2020, 12, 12),
    )
    assert {error.id for error in all_errors} == {2}


def test_get_errors_facility(errorsdb_session, superuser):
    all_errors = errors.get_errors(
        errorsdb_session,
        superuser,
        since=datetime(1970, 1, 1),
        facility="TEST_SENDING_FACILITY_2",
    )
    assert {error.id for error in all_errors} == {2}


def test_get_errors_nis(errorsdb_session, superuser):
    all_errors = errors.get_errors(
        errorsdb_session, superuser, since=datetime(1970, 1, 1), nis=["999999999"]
    )
    assert {error.id for error in all_errors} == {1}


def test_get_error_superuser(errorsdb_session, superuser):
    error = errors.get_error(errorsdb_session, 1, superuser)
    assert error
    assert error.id == 1


def test_get_error_user(errorsdb_session, test_user):
    error = errors.get_error(errorsdb_session, 1, test_user)
    assert error
    assert error.id == 1


def test_get_error_user_denied(errorsdb_session, test_user):
    with pytest.raises(PermissionsError):
        errors.get_error(errorsdb_session, 2, test_user)
