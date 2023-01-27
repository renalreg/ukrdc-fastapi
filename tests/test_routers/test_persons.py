from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, PersonSchema


async def test_person_detail(client_superuser):
    response = await client_superuser.get(f"{configuration.base_url}/persons/1")
    assert response.status_code == 200
    person = PersonSchema(**response.json())
    assert person.id == 1


async def test_person_masterrecords(client_superuser, jtrace_session):
    response = await client_superuser.get(
        f"{configuration.base_url}/persons/1/masterrecords"
    )
    assert response.status_code == 200

    mrecs = [MasterRecordSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in mrecs}
    assert returned_ids == {1, 101}
