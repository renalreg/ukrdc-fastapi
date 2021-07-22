from datetime import datetime

import pytest
from ukrdc_sqla.empi import LinkRecord, MasterRecord

from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.query.mirth.merge import (
    merge_master_records,
    merge_person_into_master_record,
)


@pytest.mark.asyncio
async def test_merge_master_records(
    jtrace_session, redis_session, mirth_session, superuser, httpx_session
):
    # Create new master records
    master_record_30 = MasterRecord(
        id=30,
        status=0,
        last_updated=datetime(2021, 1, 1),
        date_of_birth=datetime(1980, 12, 12),
        nationalid="119999999",
        nationalid_type="UKRDC",
        effective_date=datetime(2021, 1, 1),
    )

    master_record_31 = MasterRecord(
        id=31,
        status=0,
        last_updated=datetime(2020, 1, 1),
        date_of_birth=datetime(1981, 12, 12),
        nationalid="229999999",
        nationalid_type="UKRDC",
        effective_date=datetime(2020, 1, 1),
    )

    # Person 3 now has 2 master records we want to merge
    jtrace_session.add(master_record_30)
    jtrace_session.add(master_record_31)
    jtrace_session.commit()

    response = await merge_master_records(
        30, 31, superuser, jtrace_session, mirth_session, redis_session
    )
    assert response.status == "success"

    # Check we are merging master records 1 and 3
    assert f"<superceding>30</superceding>" in response.message
    assert f"<superceeded>31</superceeded>" in response.message


@pytest.mark.asyncio
async def test_merge_person_into_master_record(
    jtrace_session, redis_session, mirth_session, superuser, httpx_session
):
    # Create a new master record
    master_record_30 = MasterRecord(
        id=30,
        status=0,
        last_updated=datetime(2021, 1, 1),
        date_of_birth=datetime(1980, 12, 12),
        nationalid="119999999",
        nationalid_type="UKRDC",
        effective_date=datetime(2021, 1, 1),
    )

    # Link the new master record to an existing person
    link_record_30 = LinkRecord(
        id=30,
        person_id=1,
        master_id=30,
        link_type=0,
        link_code=0,
        last_updated=datetime(2020, 3, 16),
    )

    # Person 3 now has 2 master records we want to merge
    jtrace_session.add(master_record_30)
    jtrace_session.add(link_record_30)
    jtrace_session.commit()

    response = await merge_person_into_master_record(
        1, 30, superuser, jtrace_session, mirth_session, redis_session
    )
    assert response.status == "success"

    # Check we are merging master records 1 and 3
    assert f"<superceding>1</superceding>" in response.message
    assert f"<superceeded>30</superceeded>" in response.message


@pytest.mark.asyncio
async def test_merge_master_records_permission_denied(
    jtrace_session, redis_session, mirth_session, test_user, httpx_session
):
    with pytest.raises(PermissionsError):
        await merge_master_records(
            1, 2, test_user, jtrace_session, mirth_session, redis_session
        )
