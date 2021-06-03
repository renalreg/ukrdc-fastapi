import pytest

from ukrdc_fastapi.query import persons
from ukrdc_fastapi.query.common import PermissionsError


def test_get_persons_superuser(jtrace_session, superuser):
    all_persons = persons.get_persons(jtrace_session, superuser)
    assert {person.id for person in all_persons} == {1, 2, 3, 4}


def test_get_persons_user(jtrace_session, test_user):
    all_persons = persons.get_persons(jtrace_session, test_user)
    assert {person.id for person in all_persons} == {1, 4}


def test_get_person_superuser(jtrace_session, superuser):
    record = persons.get_person(jtrace_session, 1, superuser)
    assert record
    assert record.id == 1


def test_get_person_user(jtrace_session, test_user):
    record = persons.get_person(jtrace_session, 1, test_user)
    assert record
    assert record.id == 1


def test_get_person_denied(jtrace_session, test_user):
    with pytest.raises(PermissionsError):
        persons.get_person(jtrace_session, 2, test_user)
