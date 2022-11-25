import pytest
from ukrdc_sqla.ukrdc import Code, Facility

from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.query.facilities import (
    get_facilities,
    get_facility,
    get_facility_extracts,
)
from ukrdc_fastapi.query.facilities.demographics import get_facility_demographics
from ukrdc_fastapi.query.facilities.errors import (
    get_errors_history,
    get_patients_latest_errors,
)

from ..utils import days_ago


def test_get_facilities_superuser(
    ukrdc3_session, stats_session, redis_session, superuser
):
    all_facils = get_facilities(
        ukrdc3_session, stats_session, redis_session, superuser, include_inactive=True
    )
    # Superuser should see all facilities
    assert {facil.id for facil in all_facils} == {
        "TEST_SENDING_FACILITY_1",
        "TEST_SENDING_FACILITY_2",
    }


def test_get_facilities_user(ukrdc3_session, stats_session, redis_session, test_user):
    all_facils = get_facilities(
        ukrdc3_session, stats_session, redis_session, test_user, include_inactive=True
    )
    # Test user should see only TEST_SENDING_FACILITY_1
    assert {facil.id for facil in all_facils} == {"TEST_SENDING_FACILITY_1"}


@pytest.mark.parametrize(
    "facility_code", ["TEST_SENDING_FACILITY_1", "TEST_SENDING_FACILITY_2"]
)
def test_get_facility(facility_code, ukrdc3_session, stats_session, superuser):
    facility = get_facility(
        ukrdc3_session,
        stats_session,
        facility_code,
        superuser,
    )

    assert facility.id == facility_code
    assert facility.description == f"{facility_code}_DESCRIPTION"


def test_get_facility_data_flow(ukrdc3_session, stats_session, superuser):
    facility_object = ukrdc3_session.query(Facility).get("TEST_SENDING_FACILITY_1")
    facility_object.pkb_msg_exclusions = ["MDM_T02_CP", "MDM_T02_DOC"]
    ukrdc3_session.commit()

    facility = get_facility(
        ukrdc3_session,
        stats_session,
        "TEST_SENDING_FACILITY_1",
        superuser,
    )

    assert not facility.data_flow.pkb_in
    assert facility.data_flow.pkb_out
    assert facility.data_flow.pkb_message_exclusions == ["MDM_T02_CP", "MDM_T02_DOC"]


def test_get_facility_denied(ukrdc3_session, stats_session, test_user):
    with pytest.raises(PermissionsError):
        get_facility(
            ukrdc3_session,
            stats_session,
            "TEST_SENDING_FACILITY_2",
            test_user,
        )


def test_get_facility_history(ukrdc3_session, stats_session, superuser):
    test_code = Code(
        code="TEST_SENDING_FACILITY_1", description="Test sending facility 1"
    )

    history = get_errors_history(
        ukrdc3_session,
        stats_session,
        test_code.code,
        superuser,
    )
    assert len(history) == 365
    assert history[-1].time == days_ago(1).date()
    assert history[-1].count == 1


def test_get_facility_history_range(ukrdc3_session, stats_session, superuser):
    test_code = Code(
        code="TEST_SENDING_FACILITY_1", description="Test sending facility 1"
    )

    history = get_errors_history(
        ukrdc3_session,
        stats_session,
        test_code.code,
        superuser,
        since=days_ago(0),
    )
    assert len(history) == 0

    history = get_errors_history(
        ukrdc3_session,
        stats_session,
        test_code.code,
        superuser,
        until=days_ago(5),
    )
    assert len(history) == 360

    history = get_errors_history(
        ukrdc3_session,
        stats_session,
        test_code.code,
        superuser,
        since=days_ago(5),
        until=days_ago(0),
    )
    assert len(history) == 5


def test_get_facility_history_denied(ukrdc3_session, stats_session, test_user):
    with pytest.raises(PermissionsError):
        get_errors_history(
            ukrdc3_session,
            stats_session,
            "TEST_SENDING_FACILITY_2",
            test_user,
        )


def test_get_patients_latest_errors(ukrdc3_session, errorsdb_session, test_user):
    messages = get_patients_latest_errors(
        ukrdc3_session, errorsdb_session, "TEST_SENDING_FACILITY_1", test_user
    ).all()
    assert len(messages) == 1
    assert messages[0].id == 2


def test_get_facility_demographics(ukrdc3_session, superuser):
    stats = get_facility_demographics(
        ukrdc3_session, "TEST_SENDING_FACILITY_1", superuser
    )
    assert len(stats.age_dist) == 2
    assert [point.count for point in stats.age_dist] == [1, 1]

    assert len(stats.gender_dist) == 2
    assert [point.count for point in stats.gender_dist] == [1, 1]

    assert len(stats.ethnicity_dist) == 1

    # Ensure we prefertially use the ethnicity Code.code description over free-text
    assert stats.ethnicity_dist[0].ethnicity == "ETHNICITY_GROUP_CODE_DESCRIPTION"

    assert stats.ethnicity_dist[0].count == 2


def test_get_facility_demographics_denied(ukrdc3_session, test_user):
    with pytest.raises(PermissionsError):
        get_facility_demographics(ukrdc3_session, "TEST_SENDING_FACILITY_2", test_user)


def test_get_facility_extracts(ukrdc3_session, superuser):
    extracts = get_facility_extracts(
        ukrdc3_session,
        "TEST_SENDING_FACILITY_1",
        superuser,
    )
    assert extracts.ukrdc == 2
