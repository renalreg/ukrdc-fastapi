from datetime import datetime

import pytest
from ukrdc_sqla.ukrdc import Code, Facility, ProgramMembership

from tests.conftest import UKRDCID_1
from ukrdc_fastapi.query.facilities import (
    build_facilities_list,
    get_facilities,
    get_facility,
    get_facility_extracts,
)
from ukrdc_fastapi.query.facilities.errors import (
    get_errors_history,
    query_patients_latest_errors,
)
from ukrdc_fastapi.query.facilities.reports import (
    get_facility_report_cc001,
    get_facility_report_pm001,
)
from ukrdc_fastapi.utils.cache import BasicCache, CacheKey

from ..utils import create_basic_patient, days_ago


def test_get_facilities(ukrdc3_session, errorsdb_session, redis_session):
    all_facils = get_facilities(
        ukrdc3_session,
        errorsdb_session,
        redis_session,
        include_inactive=True,
    )
    # Superuser should see all facilities
    assert {facil.id for facil in all_facils} == {
        "TSF01",
        "TSF02",
    }


def test_get_facilities_cached(ukrdc3_session, errorsdb_session, redis_session):
    # Create the cache
    BasicCache(redis_session, CacheKey.FACILITIES_LIST).set(
        build_facilities_list(
            ukrdc3_session.query(Facility), ukrdc3_session, errorsdb_session
        )
    )

    all_facils = get_facilities(
        ukrdc3_session,
        errorsdb_session,
        redis_session,
        include_inactive=True,
    )
    # Superuser should see all facilities
    assert {facil.id for facil in all_facils} == {
        "TSF01",
        "TSF02",
    }


@pytest.mark.parametrize("facility_code", ["TSF01", "TSF02"])
def test_get_facility(facility_code, ukrdc3_session, errorsdb_session):
    facility = get_facility(
        ukrdc3_session,
        errorsdb_session,
        facility_code,
    )

    assert facility.id == facility_code
    assert facility.description == f"{facility_code}_DESCRIPTION"


def test_get_facility_data_flow(ukrdc3_session, errorsdb_session):
    facility_object = ukrdc3_session.query(Facility).get("TSF01")
    facility_object.pkb_msg_exclusions = ["MDM_T02_CP", "MDM_T02_DOC"]
    ukrdc3_session.commit()

    facility = get_facility(
        ukrdc3_session,
        errorsdb_session,
        "TSF01",
    )

    assert not facility.data_flow.pkb_in
    assert facility.data_flow.pkb_out
    assert facility.data_flow.pkb_message_exclusions == ["MDM_T02_CP", "MDM_T02_DOC"]


def test_get_facility_history(ukrdc3_session, errorsdb_session):
    test_code = Code(code="TSF01", description="Test sending facility 1")

    history = get_errors_history(
        ukrdc3_session,
        errorsdb_session,
        test_code.code,
    )
    assert len(history) == 365
    assert history[-1].time == days_ago(1).date()
    assert history[-1].count == 1


def test_get_facility_history_range(ukrdc3_session, errorsdb_session):
    test_code = Code(code="TSF01", description="Test sending facility 1")

    history = get_errors_history(
        ukrdc3_session,
        errorsdb_session,
        test_code.code,
        since=days_ago(0),
    )
    assert len(history) == 0

    history = get_errors_history(
        ukrdc3_session,
        errorsdb_session,
        test_code.code,
        until=days_ago(5),
    )
    assert len(history) == 360

    history = get_errors_history(
        ukrdc3_session,
        errorsdb_session,
        test_code.code,
        since=days_ago(5),
        until=days_ago(0),
    )
    assert len(history) == 5


def test_get_patients_latest_errors(ukrdc3_session, errorsdb_session):
    messages = errorsdb_session.scalars(query_patients_latest_errors(
        ukrdc3_session, "TSF01"
    )).all()
    assert len(messages) == 1
    assert messages[0].id == 2


def test_get_patients_latest_errors_channel(ukrdc3_session, errorsdb_session):
    messages_1_1 = errorsdb_session.scalars(query_patients_latest_errors(
        ukrdc3_session,
        "TSF01",
        channels=["00000000-0000-0000-0000-111111111111"],
    )).all()
    assert len(messages_1_1) == 1

    messages_1_0 = errorsdb_session.scalars(query_patients_latest_errors(
        ukrdc3_session,
        "TSF01",
        channels=["00000000-0000-0000-0000-000000000000"],
    )).all()
    assert len(messages_1_0) == 0

    messages_2_1 = errorsdb_session.scalars(query_patients_latest_errors(
        ukrdc3_session,
        "TSF02",
        channels=["00000000-0000-0000-0000-111111111111"],
    )).all()
    assert len(messages_2_1) == 0

    messages_2_0 = errorsdb_session.scalars(query_patients_latest_errors(
        ukrdc3_session,
        "TSF02",
        channels=["00000000-0000-0000-0000-000000000000"],
    )).all()
    assert len(messages_2_0) == 1


def test_get_facility_extracts(ukrdc3_session):
    extracts = get_facility_extracts(
        ukrdc3_session,
        "TSF01",
    )
    assert extracts.ukrdc == 2


def test_get_facility_report_cc001(ukrdc3_session):
    report1 = get_facility_report_cc001(
        ukrdc3_session,
        "TSF01",
    ).all()

    # Only 1 default test record has no treatments or memberships
    assert len(report1) == 1
    assert report1[0].pid == "PYTEST04:PV:00000000A"

    report2 = get_facility_report_cc001(
        ukrdc3_session,
        "TSF02",
    ).all()

    # TSF02 has no default test records with no treatments or memberships
    assert len(report2) == 0


def test_get_facility_report_pm001(ukrdc3_session, jtrace_session):
    report1 = get_facility_report_pm001(
        ukrdc3_session,
        "TSF01",
    ).all()

    assert len(report1) == 2
    assert {record.pid for record in report1} == {
        "PYTEST01:PV:00000000A",
        "PYTEST04:PV:00000000A",
    }

    # Add a PKB membership record

    membership_test_pid = "PYTEST:PKB:1"
    create_basic_patient(
        901,
        membership_test_pid,
        UKRDCID_1,
        "888888888",
        "PKB",
        "UKRDC",
        "00000000A",
        "Star",
        "Patrick",
        datetime(1984, 3, 17),
        ukrdc3_session,
        jtrace_session,
    )

    membership_1 = ProgramMembership(
        id="MEMBERSHIP_101",
        pid=membership_test_pid,
        program_name="PKB",
        from_time=days_ago(365),
        to_time=None,
    )
    ukrdc3_session.add(membership_1)
    ukrdc3_session.commit()

    # Test again

    report1 = get_facility_report_pm001(
        ukrdc3_session,
        "TSF01",
    ).all()

    assert len(report1) == 1
    assert {record.pid for record in report1} == {"PYTEST04:PV:00000000A"}
