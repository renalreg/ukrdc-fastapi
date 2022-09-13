import datetime
from typing import Optional

from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.stats import ErrorHistory, MultipleUKRDCID

from ukrdc_fastapi.query.facilities.errors import HistoryPoint
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.empi import MasterRecordSchema
from ukrdc_fastapi.utils import daterange


class MultipleUKRDCIDGroupItem(OrmModel):
    last_updated: datetime.datetime
    master_record: MasterRecordSchema


class MultipleUKRDCIDGroup(OrmModel):
    group_id: int
    records: list[MultipleUKRDCIDGroupItem]


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

    # Get range
    range_since: datetime.date = since or datetime.date.today() - datetime.timedelta(
        days=365
    )
    range_until: datetime.date = until or datetime.date.today()

    # Get history within range
    history = (
        statsdb.query(ErrorHistory)
        .filter(ErrorHistory.date >= range_since)
        .filter(ErrorHistory.date <= range_until)
    )

    # Create an initially empty full history dictionary
    combined_history: dict[datetime.date, int] = {
        date: 0 for date in daterange(range_since, range_until)
    }

    # For each non-zero history point, add it to the full history
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
) -> list[MultipleUKRDCIDGroup]:
    """
    Fetch groups of records corresponding to multiple UKRDC IDs for a single patient.
    Returns a list of lists of records, where the inner lists are groups of records.

    Args:
        statsdb (Session): Stats database session.
        jtrace (Session): JTrace database session.

    Returns:
        list[list[MasterRecord]]: List of groups of records.
    """
    # Fetch all unresolved rows
    record_groups = {
        item.master_id: item
        for item in statsdb.query(MultipleUKRDCID).filter(
            # pylint: disable=singleton-comparison
            MultipleUKRDCID.resolved
            == False
        )
    }

    # Fetch MasterRecord objects for each row, and key with record ID
    # This is another case of sacrificing memory for speed. We assume
    # that the number of records is small enough to fit in memory, meaning
    # that we can avoid many small JTRACE queries.
    records: dict[int, MasterRecord] = {
        record.id: record
        for record in jtrace.query(MasterRecord).filter(
            MasterRecord.id.in_(record_groups.keys())
        )
    }

    # Sort each fetched MasterRecord into groups
    item_groups: dict[int, list[MultipleUKRDCIDGroupItem]] = {}
    for master_id, item in record_groups.items():
        record = records.get(master_id)
        if record:
            group_item = MultipleUKRDCIDGroupItem(
                last_updated=item.last_updated, master_record=record
            )
            if item.group_id in item_groups:
                item_groups[item.group_id].append(group_item)
            else:
                item_groups[item.group_id] = [group_item]

    return [
        MultipleUKRDCIDGroup(group_id=group_id, records=records)
        for group_id, records in item_groups.items()
    ]
