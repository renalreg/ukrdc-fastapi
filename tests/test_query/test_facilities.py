import datetime

import pytest

from ukrdc_fastapi.query import facilities
from ukrdc_fastapi.query.common import PermissionsError


def test_get_facilities_superuser(ukrdc3_session, redis_session, superuser):
    all_facils = facilities.get_facilities(ukrdc3_session, redis_session, superuser)
    # Superuser should see all facilities
    assert {facil.id for facil in all_facils} == {
        "TEST_SENDING_FACILITY_1",
        "TEST_SENDING_FACILITY_2",
    }


def test_get_facilities_user(ukrdc3_session, redis_session, test_user):
    all_facils = facilities.get_facilities(ukrdc3_session, redis_session, test_user)
    # Test user should see only TEST_SENDING_FACILITY_1
    assert {facil.id for facil in all_facils} == {"TEST_SENDING_FACILITY_1"}


def test_get_facilities_caching(ukrdc3_session, redis_session, superuser):
    redis_session.delete("ukrdc3:facilities")

    all_facils_1 = facilities.get_facilities(ukrdc3_session, redis_session, superuser)
    all_facils_2 = facilities.get_facilities(ukrdc3_session, redis_session, superuser)

    assert all_facils_1 == all_facils_2


def test_get_facilities_empty_cache(ukrdc3_session, redis_session, superuser):
    redis_session.set("ukrdc3:facilities", "")
    all_facils = facilities.get_facilities(ukrdc3_session, redis_session, superuser)
    assert all_facils == []


def test_get_facility(ukrdc3_session, errorsdb_session, redis_session, superuser):
    facility = facilities.get_facility(
        ukrdc3_session,
        errorsdb_session,
        redis_session,
        "TEST_SENDING_FACILITY_1",
        superuser,
    )
    assert facility.id == "TEST_SENDING_FACILITY_1"


def test_get_facility_caching(
    ukrdc3_session, errorsdb_session, redis_session, superuser
):
    redis_session.delete("ukrdc3:facilities:TEST_SENDING_FACILITY_1:statistics")

    facility_1 = facilities.get_facility(
        ukrdc3_session,
        errorsdb_session,
        redis_session,
        "TEST_SENDING_FACILITY_1",
        superuser,
    )

    facility_2 = facilities.get_facility(
        ukrdc3_session,
        errorsdb_session,
        redis_session,
        "TEST_SENDING_FACILITY_1",
        superuser,
    )

    assert facility_1.statistics == facility_2.statistics


def test_get_facility_denied(
    ukrdc3_session, errorsdb_session, redis_session, test_user
):
    with pytest.raises(PermissionsError):
        facilities.get_facility(
            ukrdc3_session,
            errorsdb_session,
            redis_session,
            "TEST_SENDING_FACILITY_2",
            test_user,
        )


def test_get_facility_history(
    ukrdc3_session, errorsdb_session, redis_session, superuser
):
    history = facilities.get_errors_history(
        ukrdc3_session,
        errorsdb_session,
        redis_session,
        "TEST_SENDING_FACILITY_1",
        superuser,
    )
    assert len(history) == 1
    assert history[0].time == datetime.date(2021, 1, 1)
    assert history[0].count == 1


def test_get_facility_history_caching(
    ukrdc3_session, errorsdb_session, redis_session, superuser
):
    redis_session.delete("ukrdc3:facilities:TEST_SENDING_FACILITY_1:errorhistory")

    history_1 = facilities.get_errors_history(
        ukrdc3_session,
        errorsdb_session,
        redis_session,
        "TEST_SENDING_FACILITY_1",
        superuser,
    )

    history_2 = facilities.get_errors_history(
        ukrdc3_session,
        errorsdb_session,
        redis_session,
        "TEST_SENDING_FACILITY_1",
        superuser,
    )

    assert history_1 == history_2


def test_get_facility_history_range(
    ukrdc3_session, errorsdb_session, redis_session, superuser
):
    history = facilities.get_errors_history(
        ukrdc3_session,
        errorsdb_session,
        redis_session,
        "TEST_SENDING_FACILITY_1",
        superuser,
        since=datetime.date(2021, 1, 2),
    )
    assert len(history) == 0

    history = facilities.get_errors_history(
        ukrdc3_session,
        errorsdb_session,
        redis_session,
        "TEST_SENDING_FACILITY_1",
        superuser,
        until=datetime.date(2020, 12, 31),
    )
    assert len(history) == 0

    history = facilities.get_errors_history(
        ukrdc3_session,
        errorsdb_session,
        redis_session,
        "TEST_SENDING_FACILITY_1",
        superuser,
        since=datetime.date(2020, 12, 31),
        until=datetime.date(2021, 1, 2),
    )
    assert len(history) == 1
