import pytest

from ukrdc_fastapi.query import masterrecords
from ukrdc_fastapi.query.common import PermissionsError


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


def test_masterrecord_related_exclude_self(jtrace_session, superuser):
    records = masterrecords.get_masterrecords_related_to_masterrecord(
        jtrace_session, 1, superuser, exclude_self=True
    )

    # Check MR3 is identified as related to MR1
    assert {record.id for record in records} == {4, 101, 104}


def test_masterrecord_related_filter_nationalid_type(jtrace_session, superuser):
    records = masterrecords.get_masterrecords_related_to_masterrecord(
        jtrace_session, 1, superuser, nationalid_type="UKRDC"
    )

    # Check MR3 is identified as related to MR1
    assert {record.id for record in records} == {1, 4}


def test_masterrecord_related_exclude_self_filter_nationalid_type(
    jtrace_session, superuser
):
    records = masterrecords.get_masterrecords_related_to_masterrecord(
        jtrace_session, 1, superuser, exclude_self=True, nationalid_type="UKRDC"
    )

    # Check MR3 is identified as related to MR1
    assert {record.id for record in records} == {4}
