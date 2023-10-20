from typing import Optional
from sqlalchemy import or_

from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.ukrdc import Code, CodeExclusion, CodeMap

from ukrdc_fastapi.exceptions import MissingCodeError
from ukrdc_fastapi.schemas.code import CodeMapSchema, CodeSchema


class ExtendedCodeSchema(CodeSchema):
    maps_to: list[CodeMapSchema]
    mapped_by: list[CodeMapSchema]


def get_codes(
    ukrdc3: Session,
    coding_standard: Optional[list[str]] = None,
    search: Optional[str] = None,
) -> Query:
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

    if search:
        query = query.filter(
            or_(Code.code.ilike(f"%{search}%"), Code.description.ilike(f"%{search}%"))
        )

    query = query.order_by(Code.code)

    return query


def get_code(ukrdc3: Session, coding_standard: str, code: str) -> ExtendedCodeSchema:
    """Get details and mappings for a particular code

    Args:
        ukrdc3 (Session): SQLAlchemy session
        coding_standard (str): Coding standard
        code (str): Code

    Returns:
        ExtendedCodeSchema: Extended code details
    """
    code_obj: Optional[Code] = ukrdc3.query(Code).get((coding_standard, code))

    if not code_obj:
        raise MissingCodeError(coding_standard, code)

    maps_to = get_code_maps(
        ukrdc3,
        source_coding_standard=[code_obj.coding_standard],
        source_code=code_obj.code,
    ).all()
    mapped_by = get_code_maps(
        ukrdc3,
        destination_coding_standard=[code_obj.coding_standard],
        destination_code=code_obj.code,
    ).all()

    return ExtendedCodeSchema(
        **CodeSchema.from_orm(code_obj).dict(),
        maps_to=maps_to,
        mapped_by=mapped_by,
    )


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

    query = query.order_by(CodeMap.source_code)

    return query


def get_code_exclusions(
    ukrdc3: Session,
    coding_standard: Optional[list[str]] = None,
    code: Optional[list[str]] = None,
    system: Optional[list[str]] = None,
) -> Query:
    """Get the list of code exclusions

    Args:
        ukrdc3 (Session): SQLAlchemy session
        coding_standard (Optional[list[str]]): Coding standards to filter by. Defaults to None.
        code (Optional[list[str]]): Source code to filter by. Defaults to None.
        system (Optional[list[str]]): Excluded systems to filter by. Defaults to None.

    Returns:
        Query: Code exclusions
    """
    query = ukrdc3.query(CodeExclusion)

    if coding_standard:
        query = query.filter(CodeExclusion.coding_standard.in_(coding_standard))

    if code:
        query = query.filter(CodeExclusion.code.in_(code))

    if system:
        query = query.filter(CodeExclusion.system.in_(system))

    query = query.order_by(CodeExclusion.code)

    return query


def get_coding_standards(ukrdc3: Session) -> list[str]:
    """Get a list of available coding standards

    Args:
        ukrdc3 (Session): SQLAlchemy session

    Returns:
        list[str]: List of coding standards
    """
    query = ukrdc3.query(Code.coding_standard).distinct().order_by(Code.coding_standard)
    standards = [code.coding_standard for code in query]
    return standards
