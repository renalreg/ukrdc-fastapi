import pytest
from ukrdc_sqla.empi import MasterRecord, Person

from ukrdc_fastapi.query.mirth.unlink import unlink_person_from_master_record


@pytest.mark.asyncio
async def test_unlink_person_from_master_record(
    jtrace_session, redis_session, mirth_session, superuser
):
    response = await unlink_person_from_master_record(
        jtrace_session.query(Person).get(4),
        jtrace_session.query(MasterRecord).get(1),
        "comment",
        "user",
        jtrace_session,
        mirth_session,
        redis_session,
    )

    # First remaining link should be the original person 4 to MR 4
    assert response.id == 4
