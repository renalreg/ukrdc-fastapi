"""
The intention is that this will eventually be broken into a separately published library,
hence the slightly odd inline structure.
"""

from typing import Any, Dict, Optional

from fastapi import HTTPException
from fastapi.openapi.models import OAuth2 as OAuth2Model
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param
from okta_jwt_verifier import BaseJWTVerifier
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED


class OktaJWTBearer(SecurityBase):
    def __init__(
        self,
        issuer: str,
        audience: str,
        client_ids: list[str],
        scopes: Optional[dict[str, str]] = None,
        scheme_name: Optional[str] = None,
        description: Optional[str] = None,
        auto_error: Optional[bool] = True,
    ):
        # Parameters for JWT validation
        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.client_ids = client_ids

        self.verifier = BaseJWTVerifier(issuer=self.issuer, audience=self.audience)

        # Flows and scopes for Swagger UI
        if not scopes:
            scopes = {}

        # Currently we only allow authorizationCode flow. Others can be added later.
        flows = OAuthFlowsModel(
            authorizationCode={
                "authorizationUrl": f"{self.issuer}/v1/authorize",
                "tokenUrl": f"{self.issuer}/v1/token",
                "refreshUrl": f"{self.issuer}/v1/token",
                "scopes": scopes,
            }
        )
        self.model = OAuth2Model(flows=flows, description=description)
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[Dict[str, Any]]:
        # Fetch authorization header
        authorization: str = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        # Verify authorization header
        if not (authorization and scheme and credentials):
            if self.auto_error:  # pylint: disable=no-else-raise
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated"
                )
            else:
                return None
        if scheme.lower() != "bearer":
            if self.auto_error:  # pylint: disable=no-else-raise
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )
            else:
                return None
        # Validate the token
        try:
            await self.verifier.verify_access_token(credentials)
            _, claims, _, _ = self.verifier.parse_token(credentials)
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, detail="Invalid authentication token"
            ) from e

        return claims
