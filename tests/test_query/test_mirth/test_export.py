import pytest
from ukrdc_sqla.ukrdc import ProgramMembership

from tests.utils import days_ago
from ukrdc_fastapi.query.mirth import export


@pytest.mark.asyncio
async def test_export_all_to_pv(
    ukrdc3_session, redis_session, mirth_session, superuser
):
    response = await export.export_all_to_pv(
        "PYTEST01:PV:00000000A", superuser, ukrdc3_session, mirth_session, redis_session
    )
    assert response.status == "success"
    assert (
        response.message
        == "<result><pid>PYTEST01:PV:00000000A</pid><tests>FULL</tests><documents>FULL</documents></result>"
    )


async def test_record_export_tests(
    ukrdc3_session, redis_session, mirth_session, superuser
):
    response = await export.export_tests_to_pv(
        "PYTEST01:PV:00000000A", superuser, ukrdc3_session, mirth_session, redis_session
    )
    assert response.status == "success"
    assert (
        response.message
        == "<result><pid>PYTEST01:PV:00000000A</pid><tests>FULL</tests></result>"
    )


async def test_record_export_docs(
    ukrdc3_session, redis_session, mirth_session, superuser
):
    response = await export.export_docs_to_pv(
        "PYTEST01:PV:00000000A", superuser, ukrdc3_session, mirth_session, redis_session
    )
    assert response.status == "success"
    assert (
        response.message
        == "<result><pid>PYTEST01:PV:00000000A</pid><documents>FULL</documents></result>"
    )


async def test_record_export_radar(
    ukrdc3_session, redis_session, mirth_session, superuser
):
    response = await export.export_all_to_radar(
        "PYTEST01:PV:00000000A", superuser, ukrdc3_session, mirth_session, redis_session
    )
    assert response.status == "success"
    assert response.message == "<result><pid>PYTEST01:PV:00000000A</pid></result>"


async def test_record_export_pkb(
    ukrdc3_session, redis_session, mirth_session, superuser
):
    # Ensure PKB membership
    PID_1 = "PYTEST01:PV:00000000A"
    membership = ProgramMembership(
        id="MEMBERSHIP_PKB",
        pid=PID_1,
        program_name="PKB",
        from_time=days_ago(365),
        to_time=None,
    )
    ukrdc3_session.add(membership)
    ukrdc3_session.commit()

    # Store responses
    messages = []

    # Iterate over each message response
    async for response in export.export_all_to_pkb(
        PID_1, superuser, ukrdc3_session, mirth_session, redis_session
    ):
        messages.append(response.message)
        assert response.status == "success"

    assert messages == [
        "<result><msg_type>ADT_A28</msg_type><pid>PYTEST01:PV:00000000A</pid></result>",
        "<result><msg_type>MDM_T02_CP</msg_type><pid>PYTEST01:PV:00000000A</pid></result>",
        "<result><msg_type>MDM_T02_DOC</msg_type><pid>PYTEST01:PV:00000000A</pid><id>DOCUMENT_PDF</id></result>",
        "<result><msg_type>MDM_T02_DOC</msg_type><pid>PYTEST01:PV:00000000A</pid><id>DOCUMENT_TXT</id></result>",
        "<result><msg_type>ORU_R01_LAB</msg_type><pid>PYTEST01:PV:00000000A</pid><id>LABORDER1</id></result>",
        "<result><msg_type>ORU_R01_LAB</msg_type><pid>PYTEST01:PV:00000000A</pid><id>LABORDER2</id></result>",
        "<result><msg_type>ORU_R01_OBS</msg_type><pid>PYTEST01:PV:00000000A</pid><id>OBSERVATION1</id></result>",
        "<result><msg_type>ORU_R01_OBS</msg_type><pid>PYTEST01:PV:00000000A</pid><id>OBSERVATION_DIA_1</id></result>",
        "<result><msg_type>ORU_R01_OBS</msg_type><pid>PYTEST01:PV:00000000A</pid><id>OBSERVATION_SYS_1</id></result>",
    ]
