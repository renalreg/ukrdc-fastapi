import pytest

from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.query.mirth import memberships


@pytest.mark.asyncio
async def test_create_pkb_membership(
    jtrace_session, redis_session, mirth_session, superuser, httpx_session
):
    response = await memberships.create_pkb_membership(
        "999999999", superuser, jtrace_session, mirth_session, redis_session
    )
    assert response.status == "success"
    assert response.message == "<result><ukrdcid>999999999</ukrdcid></result>"


@pytest.mark.asyncio
async def test_merge_master_records_permission_denied(
    jtrace_session, redis_session, mirth_session, test_user, httpx_session
):
    with pytest.raises(PermissionsError):
        await memberships.create_pkb_membership(
            "999999911", test_user, jtrace_session, mirth_session, redis_session
        )
