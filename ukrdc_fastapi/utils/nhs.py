"""
Based on https://bitbucket.renalregistry.nhs.uk/projects/RR/repos/rr-nhs/browse
Will be removed as a submodule if/when the submodule gets published to PyPI
"""

from enum import Enum
from typing import Callable, Optional, Union

MIN_CHI_NO = 101010000
MAX_CHI_NO = 3112999999

MIN_HSC_NO = 3200000010
MAX_HSC_NO = 3999999999

MIN_NHS_NO = 4000000000

NumberType = Union[str, int]


class OrganizationType(Enum):
    """Possible values for organization."""

    UNK: str = "UNK"
    CHI: str = "CHI"
    HSC: str = "HSC"
    NHS: str = "NHS"


def _chi_validator(value: str):
    return _number_validator(value, MIN_CHI_NO, MAX_CHI_NO)


def _hsc_validator(value: str):
    return _number_validator(value, MIN_HSC_NO, MAX_HSC_NO)


def _nhs_validator(value: str):
    return _number_validator(value, MIN_NHS_NO)


ORGS_NUMBER_VALIDATORS: dict[OrganizationType, Callable] = {
    OrganizationType.NHS: _nhs_validator,
    OrganizationType.CHI: _chi_validator,
    OrganizationType.HSC: _hsc_validator,
}


def _check_range(
    value: NumberType, min_value: Optional[int] = None, max_value: Optional[int] = None
):
    """Check that value falls withing min_value and max_value."""

    # min_value <= x <= max_value
    return (min_value is None or int(value) >= min_value) and (
        max_value is None or int(value) <= max_value
    )


def _number_validator(
    value: str, min_value: Optional[int], max_value: Optional[int] = None
) -> bool:
    if len(value) != 10:
        return False

    if not value.isdigit():
        return False

    check_digit = 0

    for i in range(0, 9):
        check_digit += int(value[i]) * (10 - i)

    check_digit = 11 - (check_digit % 11)

    if check_digit == 11:
        check_digit = 0

    if check_digit != int(value[9]):
        return False

    if not _check_range(value, min_value, max_value):
        return False

    return True


def normalise_number(number: str) -> str:
    """Normalise NHS/CHI/HSC Number.

    Args:
        number (string): number

    Returns:
        string: 10 characters length number string
    """
    number = number.replace(" ", "").replace("-", "").strip()

    if len(number) == 9:
        number = number.rjust(10, "0")

    return number


def valid_number(
    number: Optional[NumberType], organization: Optional[OrganizationType]
) -> bool:
    """
    Check that given number is valid for the given organization.

    Args:
        number: number to validate
        organization: instance of nhs_numbers.Organization enum

    Returns:
        True if valid, False if invalid.
    """

    if organization == OrganizationType.UNK or organization is None:
        # Assume that a number is valid if unknown organization
        return True

    if number is None:
        return False

    normalised_number: str = normalise_number(str(number))
    if not normalised_number:
        return False

    validator = ORGS_NUMBER_VALIDATORS.get(organization, None)
    if validator:
        return validator(normalised_number)
    return False


def get_organization(number: Optional[NumberType]) -> OrganizationType:
    """
    Get the organization by the given number.
    Decision is based on the range of the number.

    Args:
        number: string or int number

    Returns:
        one of the OrganizationType enum values (UNK, CHI, HSC, NHS)
    """
    if number is None:
        return OrganizationType.UNK

    normalised_number: str = normalise_number(str(number))

    if len(normalised_number) < 10:
        return OrganizationType.UNK

    if MIN_CHI_NO <= int(number) <= MAX_CHI_NO:
        return OrganizationType.CHI
    if MIN_HSC_NO <= int(number) <= MAX_HSC_NO:
        return OrganizationType.HSC
    if int(number) >= MIN_NHS_NO:
        return OrganizationType.NHS
    return OrganizationType.UNK
