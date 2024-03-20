from typing import Any, Optional

from fastapi.exceptions import HTTPException

# Permissions


class PermissionsError(HTTPException):
    def __init__(self, headers: Optional[dict[str, Any]] = None) -> None:
        super().__init__(
            403,
            detail="You do not have permission to access resources belonging to this facility.",
            headers=headers,
        )


# Resources


class ResourceNotFoundError(RuntimeError):
    """Generic base resource not found error"""


class MissingFacilityError(ResourceNotFoundError):
    """No facility configuration found for this facility code"""

    def __init__(self, facility_code: str):
        super().__init__(f"Facility {facility_code} not found")


class MissingCodeError(ResourceNotFoundError):
    """Code not found in the code system"""

    def __init__(self, coding_standard: str, code: str):
        super().__init__(f"Code {coding_standard}/{code} not found")


# PKB


class NoActiveMembershipError(RuntimeError):
    """No active membership of the required type was found on this record"""


class PKBOutboundDisabledError(RuntimeError):
    """PKB outbound sending disabled for this facility"""


# Record types


class RecordTypeError(RuntimeError):
    """Operation cannot be performed on this record type"""


# Background tasks


class TaskLockError(RuntimeError):
    """Backbground task lock could not be acquired"""


class TaskNotFoundError(RuntimeError):
    """Requested background task does not exist"""
