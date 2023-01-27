import re

import pytest
from ukrdc_sqla.ukrdc import ProgramMembership

from tests.utils import days_ago
from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.utils.tasks import TrackableTaskSchema


def _last_sent_mirth_message(httpx_mock) -> str:
    raw_message = httpx_mock.get_requests(method="POST")[-1].read().decode("utf-8")
    raw_data_matches = re.findall(r"\<rawData>(.*?)</rawData>", raw_message)
    if not raw_data_matches:
        return ""
    raw_data = raw_data_matches[-1]
    decoded_data = raw_data.replace("&lt;", "<").replace("&gt;", ">")
    return decoded_data


@pytest.mark.asyncio
async def test_record_export_data(client_superuser, httpx_mock):
    response = await client_superuser.post(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/export/pv",
        json={},
    )

    assert response.status_code == 202
    task = TrackableTaskSchema(**response.json())
    assert task.status == "pending"

    task_status = await client_superuser.get(
        f"{configuration.base_url}/tasks/{task.id}"
    )
    assert task_status.status_code == 200
    assert task_status.json().get("status") == "finished"

    assert (
        _last_sent_mirth_message(httpx_mock)
        == "<result><pid>PYTEST01:PV:00000000A</pid><tests>FULL</tests><documents>FULL</documents></result>"
    )


@pytest.mark.asyncio
async def test_record_export_tests(client_superuser, httpx_mock):
    response = await client_superuser.post(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/export/pv-tests",
        json={},
    )

    assert response.status_code == 202
    task = TrackableTaskSchema(**response.json())
    assert task.status == "pending"

    task_status = await client_superuser.get(
        f"{configuration.base_url}/tasks/{task.id}"
    )
    assert task_status.status_code == 200
    assert task_status.json().get("status") == "finished"

    assert (
        _last_sent_mirth_message(httpx_mock)
        == "<result><pid>PYTEST01:PV:00000000A</pid><tests>FULL</tests></result>"
    )


@pytest.mark.asyncio
async def test_record_export_docs(client_superuser, httpx_mock):
    response = await client_superuser.post(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/export/pv-docs",
        json={},
    )

    assert response.status_code == 202
    task = TrackableTaskSchema(**response.json())
    assert task.status == "pending"

    task_status = await client_superuser.get(
        f"{configuration.base_url}/tasks/{task.id}"
    )
    assert task_status.status_code == 200
    assert task_status.json().get("status") == "finished"

    assert (
        _last_sent_mirth_message(httpx_mock)
        == "<result><pid>PYTEST01:PV:00000000A</pid><documents>FULL</documents></result>"
    )


@pytest.mark.asyncio
async def test_record_export_radar(client_superuser, httpx_mock):
    response = await client_superuser.post(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/export/radar",
        json={},
    )

    assert response.status_code == 202
    task = TrackableTaskSchema(**response.json())
    assert task.status == "pending"

    task_status = await client_superuser.get(
        f"{configuration.base_url}/tasks/{task.id}"
    )
    assert task_status.status_code == 200
    assert task_status.json().get("status") == "finished"

    assert (
        _last_sent_mirth_message(httpx_mock)
        == "<result><pid>PYTEST01:PV:00000000A</pid></result>"
    )


@pytest.mark.asyncio
async def test_record_export_pkb(client_superuser, ukrdc3_session):
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

    response = await client_superuser.post(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/export/pkb",
        json={},
    )
    assert response.status_code == 202
    task = TrackableTaskSchema(**response.json())
    assert task.status == "pending"

    task_status = await client_superuser.get(
        f"{configuration.base_url}/tasks/{task.id}"
    )
    assert task_status.status_code == 200
    assert task_status.json().get("status") == "finished"


@pytest.mark.asyncio
async def test_record_export_pkb_no_memberships(client_superuser):
    response = await client_superuser.post(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/export/pkb",
        json={},
    )
    assert response.status_code == 202
    task = TrackableTaskSchema(**response.json())
    assert task.status == "pending"

    status_response = await client_superuser.get(
        f"{configuration.base_url}/tasks/{task.id}"
    )
    assert status_response.status_code == 200
    status_task = TrackableTaskSchema(**status_response.json())

    assert status_task.status == "failed"
    assert (
        status_task.error
        == "Patient PYTEST01:PV:00000000A has no active PKB membership"
    )
