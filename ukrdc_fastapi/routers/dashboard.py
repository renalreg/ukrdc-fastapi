from fastapi import APIRouter, Depends, Security
from fastapi_auth0 import Auth0User
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ukrdc_fastapi.auth import auth
from ukrdc_fastapi.dependencies import get_jtrace, get_ukrdc3

router = APIRouter()


class DashboardSchema(BaseModel):
    message: str


@router.get("/", response_model=DashboardSchema)
def dashboard(
    user: Auth0User = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    print(user)
    return {"message": "hello world!"}
