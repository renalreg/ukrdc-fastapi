from tests.utils import days_ago
from ukrdc_fastapi.config import configuration


async def test_record_surveys(client):
    response = await client.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/surveys"
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "questions": [
                {
                    "id": "QUESTION1",
                    "questiontypecode": "TYPECODE1",
                    "response": "RESPONSE1",
                    "questionGroup": None,
                    "questionType": None,
                    "responseText": None,
                },
                {
                    "id": "QUESTION2",
                    "questiontypecode": "TYPECODE2",
                    "response": "RESPONSE2",
                    "questionGroup": None,
                    "questionType": None,
                    "responseText": None,
                },
            ],
            "scores": [
                {"id": "SCORE1", "value": "SCORE_VALUE", "scoretypecode": "TYPECODE"}
            ],
            "levels": [
                {"id": "LEVEL1", "value": "LEVEL_VALUE", "leveltypecode": "TYPECODE"}
            ],
            "id": "SURVEY1",
            "pid": "PYTEST01:PV:00000000A",
            "surveytime": days_ago(730).isoformat(),
            "surveytypecode": "TYPECODE",
            "enteredbycode": "ENTEREDBYCODE",
            "enteredatcode": "ENTEREDATCODE",
        }
    ]
