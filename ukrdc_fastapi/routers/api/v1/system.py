import os
from typing import Optional

from fastapi import APIRouter, Security
from pydantic import BaseModel

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth

router = APIRouter(tags=["System Info"])


class UserSchema(BaseModel):
    permissions: Optional[list[str]]
    email: Optional[str]


class SystemInfoSchema(BaseModel):
    github_SHA: str = os.getenv("GITHUB_SHA", "Not Available")
    github_REF: str = os.getenv("GITHUB_REF", "Not Available")
    deployment_env: str = settings.deployment_env


@router.get("/user", response_model=UserSchema)
def system_user(user: UKRDCUser = Security(auth.get_user)):
    """Retreive basic user info"""
    return UserSchema(email=user.email, permissions=user.permissions)


@router.get(
    "/info", response_model=SystemInfoSchema, dependencies=[Security(auth.get_user)]
)
def system_info():
    """Retreive basic system info"""
    return SystemInfoSchema()
