import datetime

import pytest
from ukrdc_sqla.ukrdc import Code

from ukrdc_fastapi.query import facilities
from ukrdc_fastapi.query.common import PermissionsError


def test_get_facilities_superuser(ukrdc3_session, stats_session, superuser):
    all_facils = facilities.get_facilities(
        ukrdc3_session, stats_session, superuser, include_empty=True
    )
    # Superuser should see all facilities
    assert {facil.id for facil in all_facils} == {
        "TEST_SENDING_FACILITY_1",
        "TEST_SENDING_FACILITY_2",
    }


def test_get_facilities_user(ukrdc3_session, stats_session, test_user):
    all_facils = facilities.get_facilities(
        ukrdc3_session, stats_session, test_user, include_empty=True
    )
    # Test user should see only TEST_SENDING_FACILITY_1
    assert {facil.id for facil in all_facils} == {"TEST_SENDING_FACILITY_1"}


def test_get_facility(ukrdc3_session, errorsdb_session, stats_session, superuser):
    test_code = Code(
        code="TEST_SENDING_FACILITY_1", description="Test sending facility 1"
    )

    facility = facilities.get_facility(
        ukrdc3_session,
        errorsdb_session,
        stats_session,
        test_code.code,
        superuser,
    )
    assert facility.id == "TEST_SENDING_FACILITY_1"
    assert facility.statistics.last_updated


def test_get_facility_denied(
    ukrdc3_session, errorsdb_session, stats_session, test_user
):
    with pytest.raises(PermissionsError):
        facilities.get_facility(
            ukrdc3_session,
            errorsdb_session,
            stats_session,
            "TEST_SENDING_FACILITY_2",
            test_user,
        )


def test_get_facility_history(
    ukrdc3_session, errorsdb_session, stats_session, superuser
):
    test_code = Code(
        code="TEST_SENDING_FACILITY_1", description="Test sending facility 1"
    )

    history = facilities.get_errors_history(
        ukrdc3_session,
        stats_session,
        test_code.code,
        superuser,
    )
    assert len(history) == 1
    assert history[0].time == datetime.date(2021, 1, 1)
    assert history[0].count == 1


def test_get_facility_history_range(
    ukrdc3_session, errorsdb_session, stats_session, superuser
):
    test_code = Code(
        code="TEST_SENDING_FACILITY_1", description="Test sending facility 1"
    )

    history = facilities.get_errors_history(
        ukrdc3_session,
        stats_session,
        test_code.code,
        superuser,
        since=datetime.date(2021, 1, 2),
    )
    assert len(history) == 0

    history = facilities.get_errors_history(
        ukrdc3_session,
        stats_session,
        test_code.code,
        superuser,
        until=datetime.date(2020, 12, 31),
    )
    assert len(history) == 0

    history = facilities.get_errors_history(
        ukrdc3_session,
        stats_session,
        test_code.code,
        superuser,
        since=datetime.date(2020, 12, 31),
        until=datetime.date(2021, 1, 2),
    )
    assert len(history) == 1


def test_get_facility_history_denied(ukrdc3_session, stats_session, test_user):
    with pytest.raises(PermissionsError):
        facilities.get_errors_history(
            ukrdc3_session,
            stats_session,
            "TEST_SENDING_FACILITY_2",
            test_user,
        )
