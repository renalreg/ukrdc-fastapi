from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.query.admin import AdminCountsSchema
from ukrdc_fastapi.routers.api.admin.datahealth import WorkItemGroup
from ukrdc_fastapi.schemas.common import HistoryPoint


async def test_full_workitem_history(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/admin/workitems_history"
    )
    assert response.status_code == 200


async def test_full_workitem_history_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/admin/workitems_history"
    )
    assert response.status_code == 403


async def test_full_errors_history(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/admin/errors_history"
    )
    assert response.status_code == 200


async def test_full_errors_history_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/admin/errors_history"
    )
    assert response.status_code == 403


async def test_admin_counts(client_superuser):
    response = await client_superuser.get(f"{configuration.base_url}/admin/counts")
    assert response.status_code == 200


async def test_admin_counts_denied(client_authenticated):
    response = await client_authenticated.get(f"{configuration.base_url}/admin/counts")
    assert response.status_code == 403


async def test_datahealth_multiple_ukrdcids(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/admin/datahealth/multiple_ukrdcids"
    )
    assert response.status_code == 200


async def test_datahealth_multiple_ukrdcids_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/admin/datahealth/multiple_ukrdcids"
    )
    assert response.status_code == 403


async def test_record_workitem_counts(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/admin/datahealth/record_workitem_counts"
    )
    assert response.status_code == 200


async def test_record_workitem_counts_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/admin/datahealth/record_workitem_counts"
    )
    assert response.status_code == 403
