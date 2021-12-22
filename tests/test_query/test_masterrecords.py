import pytest

from ukrdc_fastapi.query import masterrecords
from ukrdc_fastapi.query.common import PermissionsError


def test_get_masterrecords_superuser(jtrace_session, superuser):
    all_records = masterrecords.get_masterrecords(jtrace_session, superuser)
    assert {record.id for record in all_records} == {1, 2, 3, 4, 101, 102, 103, 104}


def test_get_masterrecords_user(jtrace_session, test_user):
    all_records = masterrecords.get_masterrecords(jtrace_session, test_user)
    assert {record.id for record in all_records} == {1, 4, 101, 104}


def test_get_masterrecord_superuser(jtrace_session, superuser):
    record = masterrecords.get_masterrecord(jtrace_session, 1, superuser)
    assert record
    assert record.id == 1


def test_get_masterrecord_user(jtrace_session, test_user):
    record = masterrecords.get_masterrecord(jtrace_session, 1, test_user)
    assert record
    assert record.id == 1


def test_get_masterrecord_denied(jtrace_session, test_user):
    with pytest.raises(PermissionsError):
        masterrecords.get_masterrecord(jtrace_session, 2, test_user)


def test_masterrecord_related(jtrace_session, superuser):
    records = masterrecords.get_masterrecords_related_to_masterrecord(
        jtrace_session, 1, superuser
    )

    # Check MR3 is identified as related to MR1
    assert {record.id for record in records} == {1, 4, 101, 104}

    records_excl_self = masterrecords.get_masterrecords_related_to_masterrecord(
        jtrace_session, 1, superuser, exclude_self=True
    )

    # Check MR3 is identified as related to MR1
    assert {record.id for record in records_excl_self} == {4, 101, 104}
