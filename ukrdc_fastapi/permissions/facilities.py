from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.exceptions import PermissionsError
from ukrdc_fastapi.schemas.facility import FacilityDetailsSchema


def assert_facility_permission(facility_code: str, user: UKRDCUser):
    """
    Assert that the user has permission to access the given facility

    Args:
        facility_code (str): Facility/unit code
        user (UKRDCUser): Logged-in user

    Raises:
        PermissionsError: If the user does not have permission to access the facility
    """
    units = Permissions.unit_codes(user.permissions)
    if (Permissions.UNIT_WILDCARD not in units) and (facility_code not in units):
        raise PermissionsError()


def apply_facility_list_permissions(
    facilities: list[FacilityDetailsSchema], user: UKRDCUser
) -> list[FacilityDetailsSchema]:
    """
    Apply permissions to a list of facilities based on the user's permissions

    Args:
        facilities (list[FacilityDetailsSchema]): List of facilities
        user (UKRDCUser): Logged-in user

    Returns:
        list[FacilityDetailsSchema]: List of facilities with permissions applied
    """
    unit_permissions = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD not in unit_permissions:
        return [f for f in facilities if f.id in unit_permissions]

    return facilities
