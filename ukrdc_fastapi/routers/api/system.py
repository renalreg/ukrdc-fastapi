from typing import Optional

from fastapi import APIRouter, Depends, Security
from pydantic import Field
from sqlalchemy.orm import Session

from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.dependencies import get_usersdb
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.users import get_user_preferences, update_user_preferences
from ukrdc_fastapi.schemas.base import JSONModel
from ukrdc_fastapi.schemas.user import UserPreferences, UserPreferencesRequest

router = APIRouter(tags=["System Info"])


class UserSchema(JSONModel):
    permissions: Optional[list[str]] = Field(
        None, description="List of user permissions"
    )
    email: Optional[str] = Field(None, description="User email address")


class SystemInfoSchema(JSONModel):
    github_sha: Optional[str] = Field(
        default=configuration.github_sha,
        description="Git commit SHA of the running server version",
    )
    github_ref: Optional[str] = Field(
        default=configuration.github_ref,
        description="Git branch of the running server version",
    )
    deployment_env: str = Field(
        default=configuration.deployment_env, description="Deployment environment"
    )
    version: str = Field(default=configuration.version, description="Server version")


@router.get("/info", response_model=SystemInfoSchema)
def system_info():
    """Retreive basic system info"""
    return SystemInfoSchema()


@router.get("/user", response_model=UserSchema)
def system_user(user: UKRDCUser = Security(auth.get_user())):
    """Retreive basic user info"""
    return UserSchema(email=user.email, permissions=user.permissions)


@router.get("/user/preferences", response_model=UserPreferences)
def system_user_preferences(
    user: UKRDCUser = Security(auth.get_user()), usersdb: Session = Depends(get_usersdb)
):
    """Retreive user preferences"""
    return get_user_preferences(usersdb, user)


@router.put("/user/preferences", response_model=UserPreferences)
def update_system_user_preferences(
    prefs: UserPreferencesRequest,
    user: UKRDCUser = Security(auth.get_user()),
    usersdb: Session = Depends(get_usersdb),
):
    """Update user preferences"""
    return update_user_preferences(usersdb, user, prefs)
