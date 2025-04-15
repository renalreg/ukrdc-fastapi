import pytest

from tests.conftest import UKRDCID_1
from ukrdc_fastapi.query.mirth import memberships


@pytest.mark.asyncio
async def test_create_pkb_membership(redis_session, mirth_session):
    partner = "test_partner"
    response = await memberships.create_partner_membership_for_ukrdcid(
        UKRDCID_1, mirth_session, redis_session, partner
    )
    assert response.status == "success"
    assert (
        response.message
        == f"<request><ukrdcid>{UKRDCID_1}</ukrdcid><partner>{partner}</partner></request>"
    )
