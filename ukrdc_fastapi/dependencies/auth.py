from typing import Sequence

from fastapi import Depends
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import Field

from ukrdc_fastapi.config import settings

from .okta import OktaAccessToken, OktaAuth, OktaUserModel

__all__ = ["OktaAccessToken", "OktaAuth", "auth", "Permissions"]


class Permissions:
    """Convenience constants and functions for managing API permissions.
    The user permissions are managed as groups in Okta"""

    READ_RECORDS = "ukrdc:records:read"
    WRITE_RECORDS = "ukrdc:records:write"
    EXPORT_RECORDS = "ukrdc:records:export"
    DELETE_RECORDS = "ukrdc:records:delete"

    WRITE_EMPI = "ukrdc:empi:write"

    READ_MESSAGES = "ukrdc:messages:read"
    WRITE_MESSAGES = "ukrdc:messages:write"

    READ_WORKITEMS = "ukrdc:workitems:read"
    WRITE_WORKITEMS = "ukrdc:workitems:write"

    READ_MIRTH = "ukrdc:mirth:read"
    WRITE_MIRTH = "ukrdc:mirth:write"

    READ_CODES = "ukrdc:codes:read"
    WRITE_CODES = "ukrdc:codes:write"

    UNIT_PREFIX = "ukrdc:unit:"
    UNIT_WILDCARD = "*"

    # Rarely assigned. If assigned, only temporary.
    RAISE_EXCEPTIONS = "ukrdc:exceptions:raise"

    @classmethod
    def all(cls):
        """Return all permissions for a superuser"""
        return [
            cls.READ_RECORDS,
            cls.READ_MESSAGES,
            cls.READ_MIRTH,
            cls.READ_WORKITEMS,
            cls.READ_CODES,
            cls.WRITE_RECORDS,
            cls.WRITE_MESSAGES,
            cls.WRITE_MIRTH,
            cls.WRITE_WORKITEMS,
            cls.WRITE_CODES,
            cls.EXPORT_RECORDS,
            cls.DELETE_RECORDS,
            cls.WRITE_EMPI,
            cls.UNIT_PREFIX + cls.UNIT_WILDCARD,
        ]

    @classmethod
    def unit_codes(cls, permissions: list[str]) -> list[str]:
        """Convert user permissions into a list of unit/facility codes

        Args:
            permissions (list[str]): User permission strings

        Returns:
            list[str]: List of unit/facility codes
        """
        unit_permissions: list[str] = [
            perm for perm in permissions if perm.startswith(cls.UNIT_PREFIX)
        ]
        units = [perm.split(":")[-1] for perm in unit_permissions]
        return units


class UKRDCAccessToken(OktaAccessToken):
    permission: list[str] = Field([], alias=settings.user_permission_key)


class UKRDCUser(OktaUserModel):
    pass


class URKDCAuth(OktaAuth):
    permissions = Permissions

    async def get_units(
        self, creds: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> list[str]:
        """
        Get a list of unit codes the current user is authorized to access

        There are two distinct special cases: No units will return an empty list,
        all units will return the Permissions.UNIT_ALL object
        """
        token = await self.get_token(creds)
        available_permissions: Sequence[str] = getattr(token, self.permission_key, [])
        unit_permissions: list[str] = [
            perm
            for perm in available_permissions
            if perm.startswith(Permissions.UNIT_PREFIX)
        ]
        return [perm.split(":")[-1] for perm in unit_permissions]

    @property
    def superuser(self):
        """Generate a superuser object for internal use only

        Returns:
            UKRDCUser: User object with all available permissions
        """
        return UKRDCUser(
            id="SUPERUSER",
            email="SUPERUSER@UKRDC_FASTAPI",
            permissions=self.permissions.all(),
            scopes=["openid", "profile", "email", "offline_access"],
        )


auth = URKDCAuth(
    settings.oauth_issuer,
    settings.oauth_audience,
    [settings.app_client_id, settings.swagger_client_id],
    token_model=UKRDCAccessToken,
    user_model=UKRDCUser,
)
