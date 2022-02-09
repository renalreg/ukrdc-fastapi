from datetime import datetime
from urllib.parse import quote

from ukrdc_fastapi.config import configuration

from ..utils import create_basic_facility, create_basic_patient

TEST_NUMBERS = [
    "9434765870",
    "9434765889",
    "9434765897",
    "9434765900",
    "9434765919",
    "9434765927",
    "9434765935",
    "9434765943",
    "9434765951",
]

BUMPER = 200


def _commit_extra_patients(ukrdc3, jtrace):
    for index, number in enumerate(TEST_NUMBERS):
        nhs_number = number
        ukrdcid = 100000000 + index

        dob = datetime(1950, 1, (index + 11) % 28)
        localid = f"PYTEST:SEARCH:{number}"

        sending_facility = f"TEST_SENDING_FACILITY_{index + BUMPER}"
        sending_facility_desc = f"TEST_SENDING_FACILITY_{index + BUMPER}_DESCRIPTION"
        sending_extract = f"TEST_SENDING_EXTRACT_{index + BUMPER}"

        create_basic_facility(
            sending_facility,
            sending_facility_desc,
            ukrdc3,
        )

        create_basic_patient(
            index + BUMPER,
            number,
            ukrdcid,
            nhs_number,
            sending_facility,
            sending_extract,
            localid,
            f"SURNAME{index}",
            f"NAME{index}",
            dob,
            ukrdc3,
            jtrace,
        )


async def test_search_all(ukrdc3_session, jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        url = f"{configuration.base_url}/v1/search/?search={number}"

        response = await client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER + 100}

        url = f"{configuration.base_url}/v1/search/?search={number}&include_ukrdc=true"

        response = await client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_pid(ukrdc3_session, jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        url = f"{configuration.base_url}/v1/search/?pid={number}&include_ukrdc=true"

        response = await client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_mrn(ukrdc3_session, jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        url = f"{configuration.base_url}/v1/search/?mrn_number={number}&include_ukrdc=true"

        response = await client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_ukrdc_number(ukrdc3_session, jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, _ in enumerate(TEST_NUMBERS):
        url = f"{configuration.base_url}/v1/search/?ukrdc_number={100000000 + index}&include_ukrdc=true"

        response = await client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_facility(ukrdc3_session, jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, _ in enumerate(TEST_NUMBERS):
        url = f"{configuration.base_url}/v1/search/?facility=TEST_SENDING_FACILITY_{index + BUMPER}&include_ukrdc=true"

        response = await client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_name(ukrdc3_session, jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, _ in enumerate(TEST_NUMBERS):
        full_name = quote(f"NAME{index} SURNAME{index}")
        url = f"{configuration.base_url}/v1/search/?full_name={full_name}&include_ukrdc=true"

        response = await client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_dob(ukrdc3_session, jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, _ in enumerate(TEST_NUMBERS):
        dob = f"1950-01-{str((index + 11) % 28).zfill(2)}"
        url = f"{configuration.base_url}/v1/search/?dob={dob}&include_ukrdc=true"

        response = await client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_multiple_mrn(ukrdc3_session, jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(ukrdc3_session, jtrace_session)

    # Add extra test items
    path = f"{configuration.base_url}/v1/search/?"
    for number in TEST_NUMBERS[:5]:
        path += f"mrn_number={number}&"
    path = path.rstrip("&")

    response = await client.get(path)
    assert response.status_code == 200

    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {i + BUMPER + 100 for i in range(5)}


async def test_search_implicit_dob(ukrdc3_session, jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, _ in enumerate(TEST_NUMBERS):
        dob = f"1950-01-{str((index + 11) % 28).zfill(2)}"
        url = f"{configuration.base_url}/v1/search/?search={dob}&include_ukrdc=true"

        response = await client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_implicit_facility(ukrdc3_session, jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, _ in enumerate(TEST_NUMBERS):
        url = f"{configuration.base_url}/v1/search/?search=TEST_SENDING_FACILITY_{index + BUMPER}&include_ukrdc=true"

        response = await client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}
