from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.query import masterrecords


def test_masterrecord_related(jtrace_session):
    records = jtrace_session.scalars(
        masterrecords.select_masterrecords_related_to_masterrecord(
            jtrace_session.get(MasterRecord, 1), jtrace_session
        )
    )

    # Check MR3 is identified as related to MR1
    assert {record.id for record in records} == {1, 4, 101, 104}


def test_masterrecord_related_exclude_self(jtrace_session):
    records = jtrace_session.scalars(
        masterrecords.select_masterrecords_related_to_masterrecord(
            jtrace_session.get(MasterRecord, 1), jtrace_session, exclude_self=True
        )
    )

    # Check MR3 is identified as related to MR1
    assert {record.id for record in records} == {4, 101, 104}


def test_masterrecord_related_filter_nationalid_type(jtrace_session):
    records = jtrace_session.scalars(
        masterrecords.select_masterrecords_related_to_masterrecord(
            jtrace_session.get(MasterRecord, 1),
            jtrace_session,
            nationalid_type="UKRDC",
        )
    )

    # Check MR3 is identified as related to MR1
    assert {record.id for record in records} == {1, 4}


def test_masterrecord_related_exclude_self_filter_nationalid_type(jtrace_session):
    records = jtrace_session.scalars(
        masterrecords.select_masterrecords_related_to_masterrecord(
            jtrace_session.get(MasterRecord, 1),
            jtrace_session,
            exclude_self=True,
            nationalid_type="UKRDC",
        )
    )

    # Check MR3 is identified as related to MR1
    assert {record.id for record in records} == {4}
