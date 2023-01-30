from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.empi import MasterRecord, Person
from ukrdc_sqla.utils.links import find_related_ids


def get_persons_related_to_masterrecord(record: MasterRecord, jtrace: Session) -> Query:
    """Get a list of Person records related to a given Master Record

    Args:
        jtrace (Session): SQLAlchemy session
        record_id (int): Master Record ID

    Returns:
        Query: SQLAlchemy query of Person records
    """
    _, related_person_ids = find_related_ids(jtrace, {record.id}, set())
    return jtrace.query(Person).filter(Person.id.in_(related_person_ids))
