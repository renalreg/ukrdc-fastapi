from fastapi.routing import APIRouter
from okta.client import Client as OktaClient
from okta.models import User as OktaUser

from ukrdc_fastapi.config import settings

router = APIRouter(tags=["Management"])


class OktaUKRDCUser:
    def __init__(self, okta_user: OktaUser):
        self.user = okta_user

    def get_units(self):
        return getattr(self.user.profile, "ukrdcUnits", [])

    def get_permissions(self):
        return getattr(self.user.profile, "ukrdcPermissions", [])


@router.get("/")
async def users():
    okta_client = OktaClient(
        {
            "orgUrl": settings.okta_domain,
            "token": settings.okta_api_token,
        }
    )

    users, *_ = await okta_client.list_users()

    for okta_user in users:
        user = OktaUKRDCUser(okta_user)
        print(user.get_units())
        print(user.get_permissions())

    return ""
