from typing import Optional

from fastapi import APIRouter, Security
from pydantic import BaseModel

from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth

router = APIRouter(tags=["User Info"])


class UserSchema(BaseModel):
    permissions: Optional[list[str]]
    email: Optional[str]


@router.get("/", response_model=UserSchema)
def userinfo(user: UKRDCUser = Security(auth.get_user)):
    """Retreive basic user info"""
    return UserSchema(email=user.email, permissions=user.permissions)
