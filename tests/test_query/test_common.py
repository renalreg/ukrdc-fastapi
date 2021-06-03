from ukrdc_sqla.empi import Person

from ukrdc_fastapi.query import common


def test_person_belongs_to_units(jtrace_session):
    person = jtrace_session.query(Person).get(1)
    assert common.person_belongs_to_units(person, ["TEST_SENDING_FACILITY_1"])

    assert common.person_belongs_to_units(
        person, ["TEST_SENDING_FACILITY_1", "MADE_UP_FACILITY"]
    )

    assert not common.person_belongs_to_units(person, ["MADE_UP_FACILITY"])
