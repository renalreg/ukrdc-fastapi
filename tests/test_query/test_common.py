from ukrdc_sqla.empi import Person

from ukrdc_fastapi.query import common


def test_person_belongs_to_units(jtrace_session):
    person = jtrace_session.get(Person, 1)
    assert common.person_belongs_to_units(person, ["TSF01"])

    assert common.person_belongs_to_units(person, ["TSF01", "MADE_UP_FACILITY"])

    assert not common.person_belongs_to_units(person, ["MADE_UP_FACILITY"])
