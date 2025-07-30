import re

import pytest
from ukrdc_sqla.ukrdc import ProgramMembership

from tests.utils import days_ago
from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.exceptions import NoActiveMembershipError


def _last_sent_mirth_message(httpx_mock) -> str:
    raw_message = httpx_mock.get_requests(method="POST")[-1].read().decode("utf-8")
    raw_data_matches = re.findall(r"\<rawData>(.*?)</rawData>", raw_message)
    if not raw_data_matches:
        return ""
    raw_data = raw_data_matches[-1]
    decoded_data = raw_data.replace("&lt;", "<").replace("&gt;", ">")
    return decoded_data


@pytest.mark.asyncio
async def test_record_export_data(client_authenticated):
    response = await client_authenticated.post(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/export/pv",
        json={},
    )

    assert response.status_code == 200
    assert response.json().get("status") == "success"
    assert response.json().get("numberOfMessages") == 1


@pytest.mark.asyncio
async def test_record_export_tests(client_authenticated, httpx_mock):
    response = await client_authenticated.post(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/export/pv-tests",
        json={},
    )

    assert response.status_code == 200
    assert response.json().get("status") == "success"
    assert response.json().get("numberOfMessages") == 1


@pytest.mark.asyncio
async def test_record_export_docs(client_authenticated, httpx_mock):
    response = await client_authenticated.post(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/export/pv-docs",
        json={},
    )

    assert response.status_code == 200
    assert response.json().get("status") == "success"
    assert response.json().get("numberOfMessages") == 1


@pytest.mark.asyncio
async def test_record_export_radar(client_authenticated, httpx_mock):
    response = await client_authenticated.post(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/export/radar",
        json={},
    )

    assert response.status_code == 200
    assert response.json().get("status") == "success"
    assert response.json().get("numberOfMessages") == 1


@pytest.mark.asynccio
async def test_patient_export_mrc(client_authenticated, ukrdc3_session):
    pid_1 = "PYTEST01:PV:00000000A"
    membership = ProgramMembership(
        id="MEMBERSHIP_MRC",
        pid=pid_1,
        programname="MRC",
        fromtime=days_ago(365),
        totime=None,
    )

    ukrdc3_session.add(membership)
    ukrdc3_session.commit()

    response = await client_authenticated.post(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/export/mrc",
        json={},
    )

    assert response.status_code == 200
    assert response.json().get("status") == "success"
    assert response.json().get("numberOfMessages") == 1


@pytest.mark.asyncio
async def test_record_export_pkb(client_authenticated, ukrdc3_session):
    # Ensure PKB membership
    pid_1 = "PYTEST01:PV:00000000A"
    membership = ProgramMembership(
        id="MEMBERSHIP_PKB",
        pid=pid_1,
        programname="PKB",
        fromtime=days_ago(365),
        totime=None,
    )
    ukrdc3_session.add(membership)
    ukrdc3_session.commit()

    response = await client_authenticated.post(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/export/pkb",
        json={},
    )
    assert response.status_code == 200
    assert response.json().get("status") == "success"
    assert response.json().get("numberOfMessages") == 9


@pytest.mark.asyncio
async def test_record_export_pkb_no_memberships(client_authenticated):
    with pytest.raises(NoActiveMembershipError):
        await client_authenticated.post(
            f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/export/pkb",
            json={},
        )


@pytest.mark.parametrize("route", ["pv", "pv-tests", "pv-docs", "radar", "pkb"])
async def test_record_export_denied(client_authenticated, route):
    response = await client_authenticated.post(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/export/{route}",
        json={},
    )

    assert response.status_code == 403
