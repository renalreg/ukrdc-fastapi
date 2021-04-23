from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ukrdc_fastapi.dependencies.auth import Security, User, auth

router = APIRouter()


class UserSchema(BaseModel):
    permissions: Optional[list[str]]
    email: Optional[str]


@router.get("/", response_model=UserSchema)
def userinfo(
    user: User = Security(auth.get_user),
):
    """Retreive basic user info"""
    return {"email": user.email, "permissions": user.permissions}
