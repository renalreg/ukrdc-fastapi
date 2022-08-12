from typing import Optional

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session

from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.dependencies import get_usersdb
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.users import get_user_preferences, update_user_preferences
from ukrdc_fastapi.schemas.base import JSONModel
from ukrdc_fastapi.schemas.user import ReadUserPreferences, UpdateUserPreferences

router = APIRouter(tags=["System Info"])


class UserSchema(JSONModel):
    permissions: Optional[list[str]]
    email: Optional[str]


class SystemInfoSchema(JSONModel):
    github_sha: Optional[str] = configuration.github_sha
    github_ref: Optional[str] = configuration.github_ref
    deployment_env: str = configuration.deployment_env
    version: str = configuration.version


@router.get("/user/", response_model=UserSchema)
def system_user(user: UKRDCUser = Security(auth.get_user())):
    """Retreive basic user info"""
    return UserSchema(email=user.email, permissions=user.permissions)


@router.get("/user/preferences", response_model=ReadUserPreferences)
def system_user_preferences(
    user: UKRDCUser = Security(auth.get_user()), usersdb: Session = Depends(get_usersdb)
):
    """Retreive user preferences"""
    return get_user_preferences(usersdb, user)


@router.put("/user/preferences", response_model=ReadUserPreferences)
def update_system_user_preferences(
    prefs: UpdateUserPreferences,
    user: UKRDCUser = Security(auth.get_user()),
    usersdb: Session = Depends(get_usersdb),
):
    """Update user preferences"""
    return update_user_preferences(usersdb, user, prefs)


@router.get("/info/", response_model=SystemInfoSchema)
def system_info():
    """Retreive basic system info"""
    return SystemInfoSchema()
