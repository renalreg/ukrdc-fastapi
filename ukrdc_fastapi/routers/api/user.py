from typing import Optional

from fastapi import APIRouter, Security
from pydantic import BaseModel

from ukrdc_fastapi.dependencies.auth import User, auth

router = APIRouter()


class UserSchema(BaseModel):
    permissions: Optional[list[str]]
    email: Optional[str]


@router.get("/", response_model=User)
def userinfo(user=Security(auth.get_user)):
    """Retreive basic user info"""
    return user
