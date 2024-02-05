import pytest
from ukrdc_sqla.empi import WorkItem

from ukrdc_fastapi.query.mirth import workitems


@pytest.mark.asyncio
async def test_update_workitem(jtrace_session, redis_session, mirth_session):
    response = await workitems.update_workitem(
        jtrace_session.get(WorkItem, 1),
        mirth_session,
        redis_session,
        "TEST@UKRDC_FASTAPI",
        status=3,
        comment="UPDATE COMMENT",
    )

    assert response.status == "success"
    message = response.message

    assert "<workitem>1</workitem>" in message
    assert "<status>3</status>" in message
    assert "<updateDescription>UPDATE COMMENT</updateDescription>" in message
    assert "<updatedBy>TEST@UKRDC_FASTAPI</updatedBy>" in message
