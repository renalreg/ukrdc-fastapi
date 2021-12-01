from fastapi.routing import APIRouter
from okta.client import Client as OktaClient
from okta.models import User as OktaUser
from okta.models import UserStatus

from ukrdc_fastapi.config import settings

router = APIRouter(tags=["Management"])


class OktaUKRDCUser:
    def __init__(self, okta_user: OktaUser):
        self.user = okta_user

    @property
    def id(self):
        return self.user.id

    @property
    def login(self):
        return self.user.profile.login

    @property
    def email(self):
        return self.user.profile.email

    @property
    def status(self):
        return self.user.status

    @property
    def active(self):
        return self.user.status == UserStatus.ACTIVE

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

    ukrdc_users, *_ = await okta_client.list_group_users(settings.okta_ukrdc_group_id)

    for okta_user in ukrdc_users:
        user = OktaUKRDCUser(okta_user)
        if not user.active:
            continue
        print(user.id)
        print(user.email)
        print(user.get_units())
        print(user.get_permissions())

    return ""
