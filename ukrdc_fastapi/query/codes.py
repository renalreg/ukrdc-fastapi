from typing import Optional
from sqlalchemy import or_, select
from sqlalchemy.sql.selectable import Select

from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import Code, CodeExclusion, CodeMap

from ukrdc_fastapi.exceptions import MissingCodeError
from ukrdc_fastapi.schemas.code import CodeMapSchema, CodeSchema


class ExtendedCodeSchema(CodeSchema):
    maps_to: list[CodeMapSchema]
    mapped_by: list[CodeMapSchema]


def select_codes(
    coding_standard: Optional[list[str]] = None,
    search: Optional[str] = None,
) -> Select:
    """Get the list of codes from the code list

    Args:
        ukrdc3 (Session): SQLAlchemy session
        coding_standard (Optional[list[str]]): Coding standards to filter by. Defaults to None.

    Returns:
        Query: Codes
    """
    query = select(Code)

    if coding_standard:
        query = query.where(Code.coding_standard.in_(coding_standard))

    if search:
        query = query.where(
            or_(Code.code.ilike(f"%{search}%"), Code.description.ilike(f"%{search}%"))
        )

    query = query.order_by(Code.coding_standard, Code.code)

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
    code_obj: Optional[Code] = ukrdc3.get(Code, (coding_standard, code))

    if not code_obj:
        raise MissingCodeError(coding_standard, code)

    maps_to = ukrdc3.scalars(
        select_code_maps(
            source_coding_standard=[code_obj.coding_standard]
            if code_obj.coding_standard
            else [],
            source_code=code_obj.code,
        )
    ).all()
    mapped_by = ukrdc3.scalars(
        select_code_maps(
            destination_coding_standard=[code_obj.coding_standard]
            if code_obj.coding_standard
            else [],
            destination_code=code_obj.code,
        )
    ).all()

    return ExtendedCodeSchema(
        **CodeSchema.from_orm(code_obj).dict(),
        maps_to=maps_to,
        mapped_by=mapped_by,
    )


def select_code_maps(
    source_coding_standard: Optional[list[str]] = None,
    destination_coding_standard: Optional[list[str]] = None,
    source_code: Optional[str] = None,
    destination_code: Optional[str] = None,
) -> Select:
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
    query = select(CodeMap)

    if source_coding_standard:
        query = query.where(CodeMap.source_coding_standard.in_(source_coding_standard))

    if destination_coding_standard:
        query = query.where(
            CodeMap.destination_coding_standard.in_(destination_coding_standard)
        )

    if source_code:
        query = query.where(CodeMap.source_code == source_code)

    if destination_code:
        query = query.where(CodeMap.destination_code == destination_code)

    query = query.order_by(CodeMap.source_code)

    return query


def select_code_exclusions(
    coding_standard: Optional[list[str]] = None,
    code: Optional[list[str]] = None,
    system: Optional[list[str]] = None,
) -> Select:
    """Get the list of code exclusions

    Args:
        ukrdc3 (Session): SQLAlchemy session
        coding_standard (Optional[list[str]]): Coding standards to filter by. Defaults to None.
        code (Optional[list[str]]): Source code to filter by. Defaults to None.
        system (Optional[list[str]]): Excluded systems to filter by. Defaults to None.

    Returns:
        Query: Code exclusions
    """
    query = select(CodeExclusion)

    if coding_standard:
        query = query.where(CodeExclusion.coding_standard.in_(coding_standard))

    if code:
        query = query.where(CodeExclusion.code.in_(code))

    if system:
        query = query.where(CodeExclusion.system.in_(system))

    query = query.order_by(CodeExclusion.coding_standard, CodeExclusion.code)

    return query


def get_coding_standards(ukrdc3: Session) -> list[str]:
    """Get a list of available coding standards

    Args:
        ukrdc3 (Session): SQLAlchemy session

    Returns:
        list[str]: List of coding standards
    """
    query = select(Code.coding_standard).distinct().order_by(Code.coding_standard)
    return ukrdc3.scalars(query).all()
