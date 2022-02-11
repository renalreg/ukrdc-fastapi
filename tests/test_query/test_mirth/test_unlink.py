import pytest

from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.query.mirth.unlink import unlink_person_from_master_record


@pytest.mark.asyncio
async def test_unlink_person_from_master_record(
    jtrace_session, redis_session, mirth_session, superuser
):
    response = await unlink_person_from_master_record(
        4, 1, "comment", superuser, jtrace_session, mirth_session, redis_session
    )

    # First remaining link should be the original person 4 to MR 4
    assert response.id == 4


@pytest.mark.asyncio
async def test_unlink_person_from_master_record_permission_denied(
    jtrace_session, redis_session, mirth_session, test_user
):
    with pytest.raises(PermissionsError):
        await unlink_person_from_master_record(
            4, 2, "comment", test_user, jtrace_session, mirth_session, redis_session
        )
