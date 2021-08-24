import os
from typing import Optional

from fastapi import APIRouter, Security

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.schemas.base import JSONModel

router = APIRouter(tags=["System Info"])


class TestException(RuntimeError):
    pass


class UserSchema(JSONModel):
    permissions: Optional[list[str]]
    email: Optional[str]


class SystemInfoSchema(JSONModel):
    github_sha: str = os.getenv("GITHUB_SHA", "Not Available")
    github_ref: str = os.getenv("GITHUB_REF", "Not Available")
    deployment_env: str = settings.deployment_env


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


@router.post(
    "/raise/",
    status_code=204,
    dependencies=[Security(auth.permission(Permissions.RAISE_EXCEPTIONS))],
)
def system_raise(user: UKRDCUser = Security(auth.get_user)):
    """Raise a test exception"""
    raise TestException(f"A test exception was raised by {user.email}")
