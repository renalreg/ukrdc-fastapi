from ukrdc_fastapi.config import configuration


async def test_record_diagnosis(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01PV/diagnoses/diagnosis"
    )
    assert response.status_code == 200


async def test_record_diagnosis_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03PV/diagnoses/diagnosis"
    )
    assert response.status_code == 403


async def test_record_renal_diagnosis(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01PV/diagnoses/diagnosis"
    )
    assert response.status_code == 200


async def test_record_renal_diagnosis_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03PV/diagnoses/renaldiagnosis"
    )
    assert response.status_code == 403


async def test_record_cause_of_death(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01PV/diagnoses/causeofdeath"
    )
    assert response.status_code == 200


async def test_record_cause_of_death_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03PV/diagnoses/causeofdeath"
    )
    assert response.status_code == 403
