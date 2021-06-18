import pytest

from ukrdc_fastapi.query.mirth.unlink import unlink_person_from_master_record


@pytest.mark.asyncio
async def test_unlink_person_from_master_record(
    jtrace_session, redis_session, mirth_session, superuser, httpx_session
):
    response = await unlink_person_from_master_record(
        3, 1, superuser, jtrace_session, mirth_session, redis_session
    )

    assert response.status == "success"

    assert f"<masterRecord>1</masterRecord>" in response.message
    assert f"<personId>3</personId>" in response.message
    assert "<updatedBy>TEST@UKRDC_FASTAPI</updatedBy>" in response.message
    assert f"<updateDescription />" in response.message
