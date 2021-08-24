from typing import Optional

from fastapi import APIRouter, Security

from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.schemas.base import JSONModel

router = APIRouter(tags=["System Info"])


class UserSchema(JSONModel):
    permissions: Optional[list[str]]
    email: Optional[str]


class SystemInfoSchema(JSONModel):
    github_sha: str = configuration.github_sha
    github_ref: str = configuration.github_ref
    deployment_env: str = configuration.deployment_env


@router.get("/user/", response_model=UserSchema)
def system_user(user: UKRDCUser = Security(auth.get_user)):
    """Retreive basic user info"""
    return UserSchema(email=user.email, permissions=user.permissions)


@router.get(
    "/info/", response_model=SystemInfoSchema, dependencies=[Security(auth.get_user)]
)
def system_info():
    """Retreive basic system info"""
    return SystemInfoSchema()
