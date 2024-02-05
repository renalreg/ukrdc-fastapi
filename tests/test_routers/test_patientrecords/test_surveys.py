from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.patientrecord.survey import SurveySchema


async def test_record_surveys(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/surveys"
    )
    assert response.status_code == 200

    assert len(response.json()) > 0
    assert [SurveySchema(**x) for x in response.json()]


async def test_record_surveys_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/surveys"
    )
    assert response.status_code == 403
