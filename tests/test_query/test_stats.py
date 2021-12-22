from datetime import date

from ukrdc_sqla.stats import ErrorHistory, MultipleUKRDCID

from ukrdc_fastapi.query.stats import get_full_errors_history, get_multiple_ukrdcids


def test_get_full_errors_history(stats_session):
    history_test_1 = ErrorHistory(
        facility="TEST_SENDING_FACILITY_99", date=date(2021, 1, 1), count=1
    )
    history_test_2 = ErrorHistory(
        facility="TEST_SENDING_FACILITY_98", date=date(2021, 1, 2), count=1
    )

    stats_session.add(history_test_1)
    stats_session.add(history_test_2)
    stats_session.commit()

    history = get_full_errors_history(stats_session)

    d = {point.time: point.count for point in history}
    assert d[date(2021, 1, 1)] == 2
    assert d[date(2021, 1, 2)] == 1


def test_get_multiple_ukrdcids(stats_session, jtrace_session, superuser):
    # Add multiple UKRDCID rows

    row_1 = MultipleUKRDCID(
        group_id=1,
        master_id=1,
        last_updated=date(2021, 12, 22),
    )
    row_2 = MultipleUKRDCID(
        group_id=1,
        master_id=4,
        last_updated=date(2021, 12, 22),
    )
    stats_session.add(row_1)
    stats_session.add(row_2)
    stats_session.commit()

    multiple_id_groups = get_multiple_ukrdcids(stats_session, jtrace_session)
    assert len(multiple_id_groups) == 1
    assert len(multiple_id_groups[0]) == 2
    assert {record.id for record in multiple_id_groups[0]} == {1, 4}
