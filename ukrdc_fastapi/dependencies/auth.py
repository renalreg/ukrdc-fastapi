from typing import Callable, Optional, Sequence, Union

from fastapi import Depends, HTTPException
from pydantic.main import BaseModel

from ukrdc_fastapi.config import settings

from .okta import OktaJWTBearer


class Permissions:
    """Convenience constants and functions for managing API permissions.
    The user permissions are managed as groups in Okta"""

    READ_RECORDS = "ukrdc:records:read"
    WRITE_RECORDS = "ukrdc:records:write"
    EXPORT_RECORDS = "ukrdc:records:export"
    DELETE_RECORDS = "ukrdc:records:delete"

    CREATE_MEMBERSHIPS = "ukrdc:memberships:create"

    WRITE_EMPI = "ukrdc:empi:write"

    READ_MESSAGES = "ukrdc:messages:read"
    WRITE_MESSAGES = "ukrdc:messages:write"

    READ_WORKITEMS = "ukrdc:workitems:read"
    WRITE_WORKITEMS = "ukrdc:workitems:write"

    READ_MIRTH = "ukrdc:mirth:read"
    WRITE_MIRTH = "ukrdc:mirth:write"

    READ_CODES = "ukrdc:codes:read"
    WRITE_CODES = "ukrdc:codes:write"

    READ_REPORTS = "ukrdc:reports:read"

    READ_RECORDS_AUDIT = "ukrdc:audit:records:read"

    UNIT_PREFIX = "ukrdc:unit:"
    UNIT_WILDCARD = "*"

    UNIT_ALL = UNIT_PREFIX + UNIT_WILDCARD

    @classmethod
    def all(cls):
        """Return all permissions for a superuser"""
        return [
            cls.READ_RECORDS,
            cls.READ_MESSAGES,
            cls.READ_MIRTH,
            cls.READ_WORKITEMS,
            cls.READ_CODES,
            cls.READ_REPORTS,
            cls.READ_RECORDS_AUDIT,
            cls.WRITE_RECORDS,
            cls.WRITE_MESSAGES,
            cls.WRITE_MIRTH,
            cls.WRITE_WORKITEMS,
            cls.WRITE_CODES,
            cls.WRITE_EMPI,
            cls.EXPORT_RECORDS,
            cls.DELETE_RECORDS,
            cls.CREATE_MEMBERSHIPS,
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


class UKRDCUser(BaseModel):
    id: str
    cid: Optional[str] = None  # TODO:REVIEW  is this allowed
    email: str
    scopes: list[str]
    permissions: list[str]


class URKDCAuth:
    def __init__(
        self,
        issuer: str,
        audience: str,
        client_ids: list[str],
        scope_key: str = "scope",
        permission_key: str = "org.ukrdc.permissions",
    ) -> None:
        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.client_ids = client_ids

        self.okta_jwt_scheme = OktaJWTBearer(issuer, audience, client_ids)

        self.scope_key = scope_key
        self.permission_key = permission_key

    @property
    def superuser(self):
        """Generate a superuser object for internal use only

        Returns:
            UKRDCUser: User object with all available permissions
        """
        return UKRDCUser(
            id="SUPERUSER",
            email="SUPERUSER@UKRDC_FASTAPI",
            permissions=Permissions.all(),
            scopes=["openid", "profile", "email", "offline_access"],
        )

    def get_user(self):
        """
        Dependency factory to extract basic user info from a validated access token,
        and return a user object

        Returns:
            Callable: FastAPI Depends callable returning an OktaUserModel user object
        """

        async def get_user_dependency(token=Depends(self.okta_jwt_scheme)) -> UKRDCUser:
            return UKRDCUser(
                id=token.get("uid"),
                cid=token.get("cid"),
                email=token.get("sub"),
                scopes=token.get("scp", []),
                permissions=token.get(self.permission_key, []),
            )

        return get_user_dependency

    def permission(self, permission: Union[str, Sequence[str]]) -> Callable:
        """
        Dependency factory to check for the presence of a permission or set of permissions.
        Permissions are obtained from the token key set by self.permission_key, since this is
        non-standard functionality

        E.g.
        ```
        dependencies=[
            Security(auth.permission("items:read")),
        ],
        ```

        Args:
            permission (Union[str, Sequence[str]]): Permission or list of permission strings

        Returns:
            Callable: FastAPI Depends callable
        """
        permissions: Sequence[str]
        if isinstance(permission, str):
            permissions = [permission]
        else:
            permissions = permission

        async def permission_dependency(token=Depends(self.okta_jwt_scheme)):
            available_permissions: Sequence[str] = token.get(self.permission_key, [])
            for perm in permissions:
                if perm not in available_permissions:
                    raise HTTPException(
                        403,
                        detail=f'Missing "{perm}" permission',
                    )

        return permission_dependency


auth = URKDCAuth(
    settings.oauth_issuer,
    settings.oauth_audience,
    [settings.app_client_id, settings.swagger_client_id],
)
