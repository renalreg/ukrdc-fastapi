from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Select
from ukrdc_sqla.empi import MasterRecord, Person
from ukrdc_sqla.utils.links import find_related_ids


def select_persons_related_to_masterrecord(
    record: MasterRecord, jtrace: Session
) -> Select:
    """Get a list of Person records related to a given Master Record

    Args:
        jtrace (Session): SQLAlchemy session
        record (MasterRecord): Master Record ID

    Returns:
        Select: SQLAlchemy select of Person records
    """
    _, related_person_ids = find_related_ids(
        jtrace, {record.id} if record.id else set(), set()
    )
    return select(Person).where(Person.id.in_(related_person_ids))
