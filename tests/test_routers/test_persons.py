from ukrdc_fastapi.schemas.empi import MasterRecordSchema, PersonSchema
from ukrdc_fastapi.config import configuration


def test_person_detail(client):
    response = client.get(f"{configuration.base_url}/v1/persons/1")
    assert response.status_code == 200
    person = PersonSchema(**response.json())
    assert person.id == 1


def test_person_masterrecords(client, jtrace_session):
    response = client.get(f"{configuration.base_url}/v1/persons/1/masterrecords")
    assert response.status_code == 200

    mrecs = [MasterRecordSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in mrecs}
    assert returned_ids == {1, 101}
