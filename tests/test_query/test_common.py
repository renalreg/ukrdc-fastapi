from datetime import datetime

from ukrdc_sqla.empi import Person

from tests.conftest import NI_1, NI_2, UKRDCID_1, UKRDCID_2
from ukrdc_fastapi.query import common

from ..utils import create_basic_patient


def test_person_belongs_to_units(jtrace_session):
    person = jtrace_session.get(Person, 1)
    assert common.person_belongs_to_units(person, ["TSF01"])

    assert common.person_belongs_to_units(person, ["TSF01", "MADE_UP_FACILITY"])

    assert not common.person_belongs_to_units(person, ["MADE_UP_FACILITY"])


def _create_program_patients(ukrdc3_session, jtrace_session):
    create_basic_patient(
        901,
        "PYTESTPKB1",
        UKRDCID_1,
        NI_1,
        "PKB",
        "UKRDC",
        "00000000A",
        "Test",
        "Patient",
        datetime(1984, 3, 17),
        ukrdc3_session,
        jtrace_session,
    )

    create_basic_patient(
        902,
        "PYTESTRDR1",
        UKRDCID_2,
        NI_2,
        "TSF02",
        "RADAR",
        "00000000B",
        "Test",
        "Patient-Two",
        datetime(1975, 10, 9),
        ukrdc3_session,
        jtrace_session,
    )


def test_filter_nis_by_programs_no_members(ukrdc3_session):
    candidates = [NI_1, NI_2]
    assert common.filter_nis_by_programs(ukrdc3_session, candidates, ["PKB"]) == []
    assert common.filter_nis_by_programs(ukrdc3_session, candidates, ["RADAR"]) == []


def test_filter_nis_by_programs(ukrdc3_session, jtrace_session):
    _create_program_patients(ukrdc3_session, jtrace_session)
    candidates = [NI_1, NI_2]

    assert set(common.filter_nis_by_programs(ukrdc3_session, candidates, ["PKB"])) == {
        NI_1
    }
    assert set(
        common.filter_nis_by_programs(ukrdc3_session, candidates, ["RADAR"])
    ) == {NI_2}
    assert set(
        common.filter_nis_by_programs(ukrdc3_session, candidates, ["PKB", "RADAR"])
    ) == {NI_1, NI_2}


def test_filter_nis_by_programs_only_returns_candidates(ukrdc3_session, jtrace_session):
    _create_program_patients(ukrdc3_session, jtrace_session)

    # NI_2 is a RADAR member but wasn't passed in, so it must not appear
    assert set(
        common.filter_nis_by_programs(ukrdc3_session, [NI_1], ["PKB", "RADAR"])
    ) == {NI_1}

    # Candidate NIs that don't exist in ukrdc3 are dropped
    assert set(
        common.filter_nis_by_programs(ukrdc3_session, [NI_1, "NOT_A_REAL_NI"], ["PKB"])
    ) == {NI_1}


def test_filter_nis_by_programs_empty_inputs(ukrdc3_session, jtrace_session):
    _create_program_patients(ukrdc3_session, jtrace_session)

    # No candidates
    assert common.filter_nis_by_programs(ukrdc3_session, [], ["PKB", "RADAR"]) == []

    # Unknown or empty program list
    assert common.filter_nis_by_programs(ukrdc3_session, [NI_1, NI_2], ["XYZ"]) == []
    assert common.filter_nis_by_programs(ukrdc3_session, [NI_1, NI_2], []) == []
