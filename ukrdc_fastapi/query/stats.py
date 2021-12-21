import datetime
from typing import Optional

from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.stats import ErrorHistory, MultipleUKRDCID

from ukrdc_fastapi.query.facilities import HistoryPoint
from ukrdc_fastapi.schemas.empi import MasterRecordSchema


def get_full_errors_history(
    statsdb: Session,
    since: Optional[datetime.date] = None,
    until: Optional[datetime.date] = None,
) -> list[HistoryPoint]:
    """Get a combined error history by merging each facilities histories from the stats database.

    Args:
        statsdb (Session): SQLAlchemy session to the stats database.
        since (Optional[datetime.date], optional): Start date. Defaults to last 365 days.
        until (Optional[datetime.date], optional): End date. Defaults to None.

    Returns:
        list[HistoryPoint]: Error history points.
    """
    combined_history: dict[datetime.date, int] = {}

    # Default to last year
    history = statsdb.query(ErrorHistory).filter(
        ErrorHistory.date
        >= (since or (datetime.datetime.utcnow() - datetime.timedelta(days=365)))
    )

    # Optionally filter by end date
    if until:
        history = history.filter(ErrorHistory.date <= until)

    for point in history:
        if point.count:
            if point.date not in combined_history:
                combined_history[point.date] = point.count
            else:
                combined_history[point.date] += point.count

    points = [
        HistoryPoint(time=date, count=count) for date, count in combined_history.items()
    ]
    points.sort(key=lambda p: p.time)

    return points


def get_multiple_ukrdcids(
    statsdb: Session, jtrace: Session
) -> list[list[MasterRecord]]:
    # Fetch all unresolved rows
    record_groups = {
        item.master_id: item.group_id
        for item in statsdb.query(MultipleUKRDCID).filter(
            MultipleUKRDCID.resolved == False
        )
    }

    # Fetch MasterRecord objects for each row, and key with record ID
    # This is another case of sacrificing memory for speed. We assume
    # that the number of records is small enough to fit in memory, meaning
    # that we can avoid many small JTRACE queries.
    records = {
        record.id: record
        for record in jtrace.query(MasterRecord).filter(
            MasterRecord.id.in_(record_groups.keys())
        )
    }

    # Sort each fetched MasterRecord into groups
    item_groups = {}
    for master_id, group_id in record_groups.items():
        record = records.get(master_id)
        if group_id in item_groups:
            item_groups[group_id].append(record)
        else:
            item_groups[group_id] = [record]

    return list(item_groups.values())
