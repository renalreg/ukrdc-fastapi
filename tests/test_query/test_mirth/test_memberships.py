import pytest
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.exceptions import RecordTypeError
from ukrdc_fastapi.query.mirth import memberships


@pytest.mark.asyncio
async def test_create_pkb_membership(jtrace_session, redis_session, mirth_session):
    record = jtrace_session.query(MasterRecord).get(1)
    response = await memberships.create_pkb_membership_for_masterrecord(
        record, mirth_session, redis_session
    )
    assert response.status == "success"
    assert response.message == "<result><ukrdcid>999999999</ukrdcid></result>"


@pytest.mark.asyncio
async def test_create_pkb_membership_non_ukrdc(
    jtrace_session, redis_session, mirth_session
):
    record = jtrace_session.query(MasterRecord).get(101)
    with pytest.raises(RecordTypeError):
        await memberships.create_pkb_membership_for_masterrecord(
            record, mirth_session, redis_session
        )
