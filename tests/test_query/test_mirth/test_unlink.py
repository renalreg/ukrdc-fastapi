from datetime import datetime

import pytest
from ukrdc_sqla.empi import LinkRecord

from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.query.mirth.unlink import unlink_person_from_master_record
from ukrdc_fastapi.schemas.empi import LinkRecordSchema


@pytest.mark.asyncio
async def test_unlink_person_from_master_record(
    jtrace_session, redis_session, mirth_session, superuser, httpx_session
):
    # Create new link record
    link_999 = LinkRecord(
        id=999,
        person_id=3,
        master_id=1,
        link_type=0,
        link_code=0,
        last_updated=datetime(2019, 1, 1),
    )

    # Person 3 now has a link to Master Record 1
    jtrace_session.add(link_999)
    jtrace_session.commit()

    response = await unlink_person_from_master_record(
        3, 1, "comment", superuser, jtrace_session, mirth_session, redis_session
    )

    assert LinkRecordSchema.from_orm(link_999) == response


@pytest.mark.asyncio
async def test_unlink_person_from_master_record_permission_denied(
    jtrace_session, redis_session, mirth_session, test_user, httpx_session
):
    with pytest.raises(PermissionsError):
        await unlink_person_from_master_record(
            4, 2, "comment", test_user, jtrace_session, mirth_session, redis_session
        )
