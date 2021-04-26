"""
The intention is that this will eventually be broken into a separately published library,
hence the slightly odd inline structure.
"""

from typing import Callable, Sequence, Type, Union

from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OpenIdConnect,
    SecurityScopes,
)
from okta_jwt.jwt import validate_token as validate_locally
from pydantic import BaseModel


class OktaAccessToken(BaseModel):
    ver: int
    jti: str
    iss: str
    aud: str
    iat: int
    exp: int
    cid: str
    uid: str
    scp: list[str]
    sub: str


class OktaUserModel(BaseModel):
    id: str
    email: str
    scopes: list[str]
    permissions: list[str]


class OktaAuth:  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        issuer: str,
        audience: str,
        client_ids: list[str],
        scope_key: str = "scope",
        permission_key: str = "permission",
        token_model: Type[OktaAccessToken] = OktaAccessToken,
        user_model: Type[OktaUserModel] = OktaUserModel,
    ) -> None:
        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.client_ids = client_ids

        self.oidc_scheme = OpenIdConnect(
            openIdConnectUrl=f"{issuer}/.well-known/openid-configuration"
        )

        self.scope_key = scope_key
        self.permission_key = permission_key
        self.token_model = token_model
        self.user_model = user_model

    async def get_token(
        self,
        creds: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    ) -> OktaAccessToken:
        """Get a bearer token from the request headers, and validate

        Raises:
            HTTPException: Invalid token

        Returns:
            OktaAccessToken: Valid access token object
        """
        token: str = creds.credentials
        try:
            payload = self.token_model(
                **validate_locally(
                    token,
                    self.issuer,
                    self.audience,
                    self.client_ids,
                )
            )
        except Exception as e:
            raise HTTPException(403, detail="Invalid authentication token") from e

        return payload

    async def get_user(
        self, creds: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> OktaUserModel:
        """Extract basic user info from a validated access token, and return a user object

        Returns:
            OktaUserModel: User object
        """
        token = await self.get_token(creds)
        return self.user_model(
            id=token.uid,
            email=token.sub,
            scopes=token.scp,
            permissions=getattr(token, self.permission_key, []),
        )

    async def check_scopes(
        self,
        scopes: SecurityScopes,
        creds: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    ):
        """Security dependency to check the current user has a particular set of scopes

        Args:
            scopes (SecurityScopes): Requested scopes

        Raises:
            HTTPException: Missing scope
        """
        payload = await self.get_token(creds)

        for scope in scopes.scopes:
            if scope not in payload.scp:
                raise HTTPException(
                    403,
                    detail=f'Missing "{scope}" scope',
                    headers={"WWW-Authenticate": f'Bearer scope="{scopes.scope_str}"'},
                )

    def scope(self, scope: Union[str, Sequence[str]]) -> Callable:
        """Dependency factory to check for the presence of a scope or set of scopes

        E.g.
        ```
        dependencies=[
            Security(auth.scope("profile")),
        ],
        ```

        Args:
            scope (Union[str, Sequence[str]]): Scope or list of scope strings

        Returns:
            Callable: FastAPI Depends callable
        """
        scopes: list[str]
        if isinstance(scope, str):
            scopes = [scope]
        else:
            scopes = list(scope)

        async def scope_dependency(
            creds: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        ):
            security_scopes = SecurityScopes(scopes)
            await self.check_scopes(security_scopes, creds)

        return scope_dependency

    def permission(self, permission: Union[str, Sequence[str]]) -> Callable:
        """Dependency factory to check for the presence of a permission or set of permissions.
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

        async def permission_dependency(
            creds: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        ):
            token = await self.get_token(creds)

            available_permissions: Sequence[str] = getattr(
                token, self.permission_key, []
            )
            for perm in permissions:
                if perm not in available_permissions:
                    raise HTTPException(
                        403,
                        detail=f'Missing "{perm}" permission',
                    )

        return permission_dependency
