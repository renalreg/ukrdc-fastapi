from urllib.parse import quote
from ukrdc_fastapi.config import configuration
from .utils import commit_extra_patients, TEST_NUMBERS, BUMPER

# NB: We only need the jtrace session here because our test utility function to create new patients uses it.
# Long-term (post-JTRACE) it will not be required.


async def test_search_all(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for number in TEST_NUMBERS:
        url = f"{configuration.base_url}/search/records?search={number}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["pid"] for item in response.json()["items"]}
        assert returned_ids == {number}


async def test_search_pid(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for number in TEST_NUMBERS:
        url = f"{configuration.base_url}/search/records?pid={number}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["pid"] for item in response.json()["items"]}
        assert returned_ids == {number}


async def test_search_mrn(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for number in TEST_NUMBERS:
        url = f"{configuration.base_url}/search/records?mrn_number={number}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["pid"] for item in response.json()["items"]}
        assert returned_ids == {number}


async def test_search_ukrdc_number(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    for index, number in enumerate(TEST_NUMBERS):
        url = (
            f"{configuration.base_url}/search/records?ukrdc_number={100000000 + index}"
        )

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["pid"] for item in response.json()["items"]}
        assert returned_ids == {number}


async def test_search_facility_superuser(
    ukrdc3_session, jtrace_session, client_superuser
):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    for facility in ["TSF01", "TSF02"]:
        url = f"{configuration.base_url}/search/records?facility={facility}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_facilities = {item["sendingfacility"] for item in response.json()["items"]}
        assert returned_facilities == {facility}

async def test_search_extract_superuser(
    ukrdc3_session, jtrace_session, client_superuser
):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    for i, extract in enumerate(["PV", "UKRDC"]):
        url = f"{configuration.base_url}/search/records?facility=TSF0{i+1}&extract={extract}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_extracts = {item["sendingextract"] for item in response.json()["items"]}
        assert returned_extracts == {extract}

async def test_search_name(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        full_name = quote(f"NAME{index} SURNAME{index}")
        url = f"{configuration.base_url}/search/records?full_name={full_name}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["pid"] for item in response.json()["items"]}
        assert returned_ids == {number}


async def test_search_dob(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        dob = f"1950-01-{str((index + 11) % 28).zfill(2)}"
        url = f"{configuration.base_url}/search/records?dob={dob}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["pid"] for item in response.json()["items"]}
        assert returned_ids == {number}


async def test_search_multiple_mrn(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Add extra test items
    path = f"{configuration.base_url}/search/records?"

    for number in TEST_NUMBERS[:5]:
        path += f"mrn_number={number}&"

    path = path.rstrip("&")

    response = await client_superuser.get(path)
    assert response.status_code == 200

    returned_ids = {item["pid"] for item in response.json()["items"]}
    assert returned_ids == set(TEST_NUMBERS[:5])


async def test_search_implicit_dob(ukrdc3_session, jtrace_session, client_superuser):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        dob = f"1950-01-{str((index + 11) % 28).zfill(2)}"
        url = f"{configuration.base_url}/search/records?search={dob}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_ids = {item["pid"] for item in response.json()["items"]}
        assert returned_ids == {number}


async def test_search_implicit_facility(
    ukrdc3_session, jtrace_session, client_superuser
):
    # Add extra test items
    commit_extra_patients(ukrdc3_session, jtrace_session)

    for facility in ["TSF01", "TSF02"]:
        url = f"{configuration.base_url}/search/records?search={facility}"

        response = await client_superuser.get(url)
        assert response.status_code == 200

        returned_facilities = {item["sendingfacility"] for item in response.json()["items"]}
        assert returned_facilities == {facility}


async def test_search_permissions(client_authenticated):
    # Test permissions using the conftest test data
    url = f"{configuration.base_url}/search/records?facility=TSF01"
    response = await client_authenticated.get(url)
    assert response.status_code == 200
    returned_ids = {item["pid"] for item in response.json()["items"]}
    assert returned_ids == {"PYTEST04:PV:00000000A", "PYTEST01:PV:00000000A"}

    url = f"{configuration.base_url}/search/records?facility=TSF02"
    response = await client_authenticated.get(url)
    assert response.status_code == 200
    returned_ids = {item["pid"] for item in response.json()["items"]}
    assert returned_ids == set()


async def test_search_permissions_superuser(client_superuser):
    # Test permissions using the conftest test data
    url = f"{configuration.base_url}/search/records?facility=TSF01"
    response = await client_superuser.get(url)
    assert response.status_code == 200
    returned_ids = {item["pid"] for item in response.json()["items"]}
    assert returned_ids == {"PYTEST04:PV:00000000A", "PYTEST01:PV:00000000A"}

    url = f"{configuration.base_url}/search/records?facility=TSF02"
    response = await client_superuser.get(url)
    assert response.status_code == 200
    returned_ids = {item["pid"] for item in response.json()["items"]}
    assert returned_ids == {"PYTEST02:PV:00000000A"}
