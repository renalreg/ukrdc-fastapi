from urllib.parse import quote

from ukrdc_fastapi.config import configuration
from .utils import commit_extra_patients, TEST_NUMBERS, BUMPER


async def test_search_all(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        url = f"{configuration.base_url}/search?search={number}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_pid(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        url = f"{configuration.base_url}/search?pid={number}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_mrn(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        url = f"{configuration.base_url}/search?mrn_number={number}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_ukrdc_number(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, _ in enumerate(TEST_NUMBERS):
        url = f"{configuration.base_url}/search?ukrdc_number={100000000 + index}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_facility_superuser(
    ukrdc3_session, jtrace_session, client_superuser
):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, _ in enumerate(TEST_NUMBERS):
        url = f"{configuration.base_url}/search?facility=TSF{index + BUMPER}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_name(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, _ in enumerate(TEST_NUMBERS):
        full_name = quote(f"NAME{index} SURNAME{index}")
        url = f"{configuration.base_url}/search?full_name={full_name}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_dob(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, _ in enumerate(TEST_NUMBERS):
        dob = f"1950-01-{str((index + 11) % 28).zfill(2)}"
        url = f"{configuration.base_url}/search?dob={dob}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_multiple_mrn(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Add extra test items
    path = f"{configuration.base_url}/search?"
    for number in TEST_NUMBERS[:5]:
        path += f"mrn_number={number}&"
    # Exclude UKRDC records
    path += "number_type=NHS&number_type=HSC&number_type=CHI"
    path = path.rstrip("&")

    response = await client_superuser.get(path)
    assert response.status_code == 200

    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {i + BUMPER + 100 for i in range(5)}


async def test_search_implicit_dob(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, _ in enumerate(TEST_NUMBERS):
        dob = f"1950-01-{str((index + 11) % 28).zfill(2)}"
        url = f"{configuration.base_url}/search?search={dob}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_implicit_facility(
    ukrdc3_session, jtrace_session, client_superuser
):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, _ in enumerate(TEST_NUMBERS):
        url = f"{configuration.base_url}/search?search=TSF{index + BUMPER}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


async def test_search_permissions(client_authenticated):
    # Test permissions using the conftest test data
    url = f"{configuration.base_url}/search?facility=TSF01"
    response = await client_authenticated.get(url)
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1, 4, 101, 104}

    url = f"{configuration.base_url}/search?facility=TSF02"
    response = await client_authenticated.get(url)
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == set()


async def test_search_permissions_superuser(client_superuser):
    # Test permissions using the conftest test data
    url = f"{configuration.base_url}/search?facility=TSF01"
    response = await client_superuser.get(url)
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1, 4, 101, 104}

    url = f"{configuration.base_url}/search?facility=TSF02"
    response = await client_superuser.get(url)
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {2, 102}
