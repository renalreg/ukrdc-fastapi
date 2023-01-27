from ukrdc_sqla.ukrdc import LabOrder, ResultItem

from tests.utils import days_ago
from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.laborder import LabOrderSchema, LabOrderShortSchema


async def test_record_laborders(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/laborders"
    )
    assert response.status_code == 200
    orders = [LabOrderShortSchema(**item) for item in response.json()["items"]]
    assert {order.id for order in orders} == {
        "LABORDER1",
        "LABORDER2",
    }


async def test_laborder(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/laborders/LABORDER1"
    )
    assert response.status_code == 200
    order = LabOrderSchema(**response.json())
    assert order
    assert order.id == "LABORDER1"


async def test_laborder_delete(client_superuser, ukrdc3_session):
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
    assert ukrdc3_session.query(LabOrder).get("LABORDER_TEMP")
    assert ukrdc3_session.query(ResultItem).get("RESULTITEM_TEMP")
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/laborders/LABORDER_TEMP"
    )
    assert response.status_code == 200

    # Delete the lab order
    response = await client_superuser.delete(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/laborders/LABORDER_TEMP"
    )
    assert response.status_code == 204

    # Make sure the lab order was deleted
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/laborders/LABORDER_TEMP"
    )
    assert response.status_code == 404
    assert not ukrdc3_session.query(LabOrder).get("LABORDER_TEMP")
    assert not ukrdc3_session.query(ResultItem).get("RESULTITEM_TEMP")
