from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.query.admin import AdminCountsSchema
from ukrdc_fastapi.routers.api.admin.datahealth import WorkItemGroup
from ukrdc_fastapi.schemas.common import HistoryPoint


async def test_full_workitem_history(client):
    response = await client.get(f"{configuration.base_url}/admin/workitems_history")

    nonzero_points: list[HistoryPoint] = [
        HistoryPoint(**point) for point in response.json() if point.get("count") > 0
    ]
    assert len(nonzero_points) > 0


async def test_full_errors_history(client):
    response = await client.get(f"{configuration.base_url}/admin/errors_history")

    nonzero_points: list[HistoryPoint] = [
        HistoryPoint(**point) for point in response.json() if point.get("count") > 0
    ]
    assert len(nonzero_points) > 0


async def test_admin_counts(client):
    response = await client.get(f"{configuration.base_url}/admin/counts")

    counts = AdminCountsSchema(**response.json())
    assert counts.distinct_patients == 4
    assert counts.open_workitems == 3
    assert counts.patients_receiving_errors == 2


async def test_datahealth_multiple_ukrdcids(client):
    response = await client.get(
        f"{configuration.base_url}/admin/datahealth/multiple_ukrdcids"
    )
    assert response.status_code == 200

    multiple_id_groups = response.json().get("items")
    assert len(multiple_id_groups) == 1
    assert len(multiple_id_groups[0].get("records")) == 2
    assert {
        record.get("masterRecord").get("id")
        for record in multiple_id_groups[0].get("records")
    } == {1, 4}


async def test_record_workitem_counts(client):
    response = await client.get(
        f"{configuration.base_url}/admin/datahealth/record_workitem_counts"
    )
    assert response.status_code == 200

    items = [WorkItemGroup(**item) for item in response.json().get("items")]
    assert len(items) == 2

    assert items[0].master_record.id == 4
    assert items[0].work_item_count == 2
