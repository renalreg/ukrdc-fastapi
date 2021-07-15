from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.ukrdc import Code, CodeMap


def get_codes(ukrdc3: Session, coding_standard: Optional[list[str]] = None) -> Query:
    """Get the list of codes from the code list

    Args:
        ukrdc3 (Session): SQLAlchemy session
        coding_standard (Optional[list[str]]): Coding standards to filter by. Defaults to None.

    Returns:
        Query: Codes
    """
    query = ukrdc3.query(Code)

    if coding_standard:
        query = query.filter(Code.coding_standard.in_(coding_standard))

    return query


def get_code_maps(
    ukrdc3: Session,
    source_coding_standard: Optional[list[str]] = None,
    destination_coding_standard: Optional[list[str]] = None,
    source_code: Optional[str] = None,
    destination_code: Optional[str] = None,
) -> Query:
    """Get the list of codes from the code map

    Args:
        ukrdc3 (Session): SQLAlchemy session
        source_coding_standard (Optional[list[str]]): Coding standards to filter by. Defaults to None.
        destination_coding_standard (Optional[list[str]]): Coding standards to filter by. Defaults to None.
        source_code (Optional[str]): Source code to filter by. Defaults to None.
        destination_code (Optional[str]): Destination code to filter by. Defaults to None.

    Returns:
        Query: Code maps
    """
    query = ukrdc3.query(CodeMap)

    if source_coding_standard:
        query = query.filter(CodeMap.source_coding_standard.in_(source_coding_standard))

    if destination_coding_standard:
        query = query.filter(
            CodeMap.destination_coding_standard.in_(destination_coding_standard)
        )

    if source_code:
        query = query.filter(CodeMap.source_code == source_code)

    if destination_code:
        query = query.filter(CodeMap.destination_code == destination_code)

    return query


def get_coding_standards(ukrdc3: Session) -> list[str]:
    """Get a list of available coding standards

    Args:
        ukrdc3 (Session): SQLAlchemy session

    Returns:
        list[str]: List of coding standards
    """
    query = ukrdc3.query(Code.coding_standard).distinct()
    standards = [code.coding_standard for code in query]
    return standards
