from datetime import date

from ukrdc_sqla.stats import ErrorHistory

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


def test_get_multiple_ukrdcids(stats_session, jtrace_session):
    multiple_id_groups = get_multiple_ukrdcids(stats_session, jtrace_session)
    assert len(multiple_id_groups) == 1
    assert len(multiple_id_groups[0].records) == 2
    assert {record.master_record.id for record in multiple_id_groups[0].records} == {
        1,
        4,
    }
