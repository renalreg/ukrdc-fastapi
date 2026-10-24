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


def test_get_nis_for_programs(ukrdc3_session, jtrace_session):
    assert common.get_nis_for_programs(ukrdc3_session, ["PKB"]) == []
    assert common.get_nis_for_programs(ukrdc3_session, ["RADAR"]) == []

    create_basic_patient(
        901,
        "PYTEST:PKB:1",
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
        "PYTEST:RADAR:1",
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

    assert set(common.get_nis_for_programs(ukrdc3_session, ["PKB"])) == {NI_1}
    assert set(common.get_nis_for_programs(ukrdc3_session, ["RADAR"])) == {NI_2}
    assert set(common.get_nis_for_programs(ukrdc3_session, ["PKB", "RADAR"])) == {
        NI_1,
        NI_2,
    }
    assert common.get_nis_for_programs(ukrdc3_session, ["XYZ"]) == []
