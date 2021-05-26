"""
Query code snippets that are useful in more than one type of resource query
"""
from typing import Any, Optional

from fastapi.exceptions import HTTPException
from ukrdc_sqla.empi import Person, PidXRef


class PermissionsError(HTTPException):
    def __init__(self, headers: Optional[dict[str, Any]] = None) -> None:
        super().__init__(
            403,
            detail="You do not have permission to access resources belonging to this facility.",
            headers=headers,
        )


def person_belongs_to_units(person: Person, units: list[str]) -> bool:
    """Find if a Person record is associated with any of a set of unit codes

    Args:
        person (Person): Person record to check
        units (list[str]): List of unit codes

    Returns:
        bool: True if the Person is associated with a unit from the list.
    """
    xref: PidXRef
    for xref in person.xref_entries:
        if xref.sending_facility in units:
            return True
    return False
