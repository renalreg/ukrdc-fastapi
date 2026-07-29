"""
Query code snippets that are useful in more than one type of resource query
"""

from ukrdc_sqla.empi import Person


def person_belongs_to_units(person: Person, units: list[str]) -> bool:
    """Find if a Person record is associated with any of a set of unit codes

    Args:
        person (Person): Person record to check
        units (list[str]): List of unit codes

    Returns:
        bool: True if the Person is associated with a unit from the list.
    """
    return any(xref.sending_facility in units for xref in person.xref_entries)
