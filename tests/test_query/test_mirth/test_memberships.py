import pytest

from tests.conftest import UKRDCID_1
from ukrdc_fastapi.query.mirth import memberships


@pytest.mark.asyncio
async def test_create_pkb_membership(redis_session, mirth_session):
    response = await memberships.create_pkb_membership_for_ukrdcid(
        UKRDCID_1, mirth_session, redis_session
    )
    assert response.status == "success"
    assert response.message == f"<result><ukrdcid>{UKRDCID_1}</ukrdcid></result>"
