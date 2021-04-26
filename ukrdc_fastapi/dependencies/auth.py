from ukrdc_fastapi.config import settings

from .okta import OktaAccessToken, OktaAuth
from .okta import OktaUserModel as User

__all__ = ["OktaAccessToken", "OktaAuth", "User", "auth", "Permissions"]


class UKRDCAccessToken(OktaAccessToken):
    ukrdc: list[str]


auth = OktaAuth(
    settings.oauth_issuer,
    settings.oauth_audience,
    [settings.app_client_id, settings.swagger_client_id],
    token_model=UKRDCAccessToken,
    permission_key="ukrdc",
)


class Permissions:
    """Convenience constants and functions for managing API permissions.
    The user permissions are managed as groups in Okta"""

    READ_PATIENTRECORDS = "ukrdc:records:read"
    WRITE_PATIENTRECORDS = "ukrdc:records:write"
    READ_EMPI = "ukrdc:empi:read"
    WRITE_EMPI = "ukrdc:empi:write"
    READ_WORKITEMS = "ukrdc:workitems:read"
    WRITE_WORKITEMS = "ukrdc:workitems:write"
    READ_MIRTH = "ukrdc:mirth:read"
    WRITE_MIRTH = "ukrdc:mirth:write"

    @classmethod
    def all(cls, as_string: bool = False):
        """Return an array of all possible scopes"""
        arr: list[str] = [
            cls.READ_PATIENTRECORDS,
            cls.READ_EMPI,
            cls.READ_MIRTH,
            cls.READ_WORKITEMS,
            cls.WRITE_PATIENTRECORDS,
            cls.WRITE_EMPI,
            cls.WRITE_MIRTH,
            cls.WRITE_WORKITEMS,
        ]
        if not as_string:
            return arr
        return " ".join(arr)
