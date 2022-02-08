import pytest
from ukrdc_sqla.ukrdc import Code, Facility

from ukrdc_fastapi.query import facilities
from ukrdc_fastapi.query.common import PermissionsError

from ..utils import days_ago


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


def test_get_facility(ukrdc3_session, stats_session, superuser):
    facility = facilities.get_facility(
        ukrdc3_session,
        stats_session,
        "TEST_SENDING_FACILITY_1",
        superuser,
    )

    assert facility.id == "TEST_SENDING_FACILITY_1"
    assert facility.description == "TEST_SENDING_FACILITY_1_DESCRIPTION"
    assert facility.statistics.last_updated


def test_get_facility_data_flow(ukrdc3_session, stats_session, superuser):
    facility_object = ukrdc3_session.query(Facility).get("TEST_SENDING_FACILITY_1")
    facility_object.pkb_msg_exclusions = ["MDM_T02_CP", "MDM_T02_DOC"]
    ukrdc3_session.commit()

    facility = facilities.get_facility(
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
        facilities.get_facility(
            ukrdc3_session,
            stats_session,
            "TEST_SENDING_FACILITY_2",
            test_user,
        )


def test_get_facility_history(ukrdc3_session, stats_session, superuser):
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
    assert history[0].time == days_ago(1).date()
    assert history[0].count == 1


def test_get_facility_history_range(ukrdc3_session, stats_session, superuser):
    test_code = Code(
        code="TEST_SENDING_FACILITY_1", description="Test sending facility 1"
    )

    history = facilities.get_errors_history(
        ukrdc3_session,
        stats_session,
        test_code.code,
        superuser,
        since=days_ago(0),
    )
    assert len(history) == 0

    history = facilities.get_errors_history(
        ukrdc3_session,
        stats_session,
        test_code.code,
        superuser,
        until=days_ago(5),
    )
    assert len(history) == 0

    history = facilities.get_errors_history(
        ukrdc3_session,
        stats_session,
        test_code.code,
        superuser,
        since=days_ago(5),
        until=days_ago(0),
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


def test_get_patients_latest_errors(
    ukrdc3_session, stats_session, errorsdb_session, test_user
):
    messages = facilities.get_patients_latest_errors(
        ukrdc3_session,
        errorsdb_session,
        stats_session,
        "TEST_SENDING_FACILITY_1",
        test_user,
    ).all()
    assert len(messages) == 1
    assert messages[0].id == 3
