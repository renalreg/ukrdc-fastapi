from ukrdc_sqla.ukrdc import LabOrder, ResultItem

from tests.utils import days_ago
from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.patientrecord.laborder import LabOrderShortSchema


async def test_record_laborders(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/laborders"
    )
    assert response.status_code == 200

    items = response.json().get("items", [])
    assert len(items) > 0
    assert [LabOrderShortSchema(**x) for x in items]


async def test_record_laborders_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/laborders"
    )
    assert response.status_code == 403


async def test_laborder(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/laborders/LABORDER1"
    )
    assert response.status_code == 200


async def test_laborder_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/laborders/LABORDER1"
    )
    assert response.status_code == 403


async def test_laborder_delete(client_authenticated, ukrdc3_session):
    laborder = LabOrder(
        id="LABORDER_TEMP",
        pid="PYTEST01:PV:00000000A",
        external_id="EXTERNAL_ID_TEMP",
        order_category="ORDER_CATEGORY_TEMP",
        specimen_collected_time=days_ago(365),
    )
    resultitem = ResultItem(
        id="RESULTITEM_TEMP",
        order_id="LABORDER_TEMP",
        service_id_std="SERVICE_ID_STD_TEMP",
        service_id="SERVICE_ID_TEMP",
        service_id_description="SERVICE_ID_DESCRIPTION_TEMP",
        value="VALUE_TEMP",
        value_units="VALUE_UNITS_TEMP",
        observation_time=days_ago(365),
    )
    ukrdc3_session.add(laborder)
    ukrdc3_session.add(resultitem)
    ukrdc3_session.commit()

    # Make sure the laborder was created
    assert ukrdc3_session.get(LabOrder, "LABORDER_TEMP")
    assert ukrdc3_session.get(ResultItem, "RESULTITEM_TEMP")
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/laborders/LABORDER_TEMP"
    )
    assert response.status_code == 200

    # Delete the lab order
    response = await client_authenticated.delete(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/laborders/LABORDER_TEMP"
    )
    assert response.status_code == 204

    # Make sure the lab order was deleted
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/laborders/LABORDER_TEMP"
    )
    assert response.status_code == 404
    assert not ukrdc3_session.get(LabOrder, "LABORDER_TEMP")
    assert not ukrdc3_session.get(ResultItem, "RESULTITEM_TEMP")


async def test_laborder_delete_denied(client_authenticated):
    response = await client_authenticated.delete(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/laborders/LABORDER1"
    )
    assert response.status_code == 403
