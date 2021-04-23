from fastapi import Security
from fastapi_auth0 import Auth0
from fastapi_auth0 import Auth0User as User
from fastapi_auth0 import auth0_rule_namespace

__all__ = ["Security", "User", "auth", "Scopes", "auth0_rule_namespace"]

auth = Auth0(
    domain="renalreg.eu.auth0.com", api_audience="https://app.ukrdc.org/api", scopes={}
)


class Scopes:
    """Convenience constants and functions for managing API scopes.
    The user scopes/permissions are managed via Auth0"""

    READ_PATIENTRECORDS = "read:patientrecords"
    WRITE_PATIENTRECORDS = "write:patientrecords"
    READ_EMPI = "read:empi"
    WRITE_EMPI = "write:empi"
    READ_WORKITEMS = "read:workitems"
    WRITE_WORKITEMS = "write:workitems"
    READ_MIRTH = "read:mirth"
    WRITE_MIRTH = "write:mirth"

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
