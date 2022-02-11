import pytest
from ukrdc_sqla.ukrdc import ProgramMembership

from tests.utils import days_ago
from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.tasks.background import TrackableTaskSchema


async def test_record_export_data(client):
    response = await client.post(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A/export/pv/",
        json={},
    )
    assert response.json() == {
        "message": "<result><pid>PYTEST01:PV:00000000A</pid><tests>FULL</tests><documents>FULL</documents></result>",
        "status": "success",
    }


async def test_record_export_tests(client):
    response = await client.post(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A/export/pv-tests/",
        json={},
    )
    assert response.json() == {
        "status": "success",
        "message": "<result><pid>PYTEST01:PV:00000000A</pid><tests>FULL</tests></result>",
    }


async def test_record_export_docs(client):
    response = await client.post(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A/export/pv-docs/",
        json={},
    )
    assert response.json() == {
        "message": "<result><pid>PYTEST01:PV:00000000A</pid><documents>FULL</documents></result>",
        "status": "success",
    }


async def test_record_export_radar(client):
    response = await client.post(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A/export/radar/",
        json={},
    )
    assert response.json() == {
        "message": "<result><pid>PYTEST01:PV:00000000A</pid></result>",
        "status": "success",
    }


@pytest.mark.asyncio
async def test_record_export_pkb(client, ukrdc3_session):
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

    response = await client.post(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A/export/pkb/",
        json={},
    )
    assert response.status_code == 202
    task = TrackableTaskSchema(**response.json())
    assert task.status == "pending"

    task_status = await client.get(f"{configuration.base_url}/v1/tasks/{task.id}/")
    assert task_status.status_code == 200
    assert task_status.json().get("status") == "finished"


@pytest.mark.asyncio
async def test_record_export_pkb_no_memberships(client):
    response = await client.post(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A/export/pkb/",
        json={},
    )
    assert response.status_code == 202
    task = TrackableTaskSchema(**response.json())
    assert task.status == "pending"

    status_response = await client.get(f"{configuration.base_url}/v1/tasks/{task.id}/")
    assert status_response.status_code == 200
    status_task = TrackableTaskSchema(**status_response.json())

    assert status_task.status == "failed"
    assert (
        status_task.error
        == "Patient PYTEST01:PV:00000000A has no active PKB membership"
    )
