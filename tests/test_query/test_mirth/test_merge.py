from datetime import datetime

import pytest
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.query.mirth.merge import merge_master_records

from ...utils import days_ago


@pytest.mark.asyncio
async def test_merge_master_records(jtrace_session, redis_session, mirth_session):
    # Create new master records
    master_record_30 = MasterRecord(
        id=30,
        status=0,
        last_updated=days_ago(0),
        date_of_birth=datetime(1980, 12, 12),
        nationalid="119999999",
        nationalid_type="UKRDC",
        effective_date=days_ago(0),
    )

    master_record_31 = MasterRecord(
        id=31,
        status=0,
        last_updated=days_ago(0),
        date_of_birth=datetime(1981, 12, 12),
        nationalid="229999999",
        nationalid_type="UKRDC",
        effective_date=days_ago(0),
    )

    # Person 3 now has 2 master records we want to merge
    jtrace_session.add(master_record_30)
    jtrace_session.add(master_record_31)
    jtrace_session.commit()

    response = await merge_master_records(
        master_record_30, master_record_31, mirth_session, redis_session
    )
    assert response.status == "success"

    # Check we are merging master records 1 and 3
    assert "<superceding>30</superceding>" in response.message
    assert "<superceeded>31</superceeded>" in response.message
