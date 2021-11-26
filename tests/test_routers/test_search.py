from datetime import date, datetime

from stdnum.gb import nhs
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person, PidXRef

from ..utils import create_basic_patient

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
        ukrdcid = f"{number}-{index}"

        dob = datetime(1950, 1, (index + 11) % 28)
        localid = f"PYTEST:SEARCH:{number}"

        create_basic_patient(
            index + BUMPER,
            localid,
            ukrdcid,
            nhs_number,
            "TEST_SENDING_FACILITY_1",
            "TEST_SENDING_EXTRACT_1",
            localid,
            f"NAME{index}",
            f"SURNAME{index}",
            dob,
            ukrdc3,
            jtrace,
        )


def test_search_all(ukrdc3_session, jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        url = f"/api/v1/search/?search={number}"

        response = client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER + 100}

        url = f"/api/v1/search/?search={number}&include_ukrdc=true"

        response = client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


def test_search_mrn(ukrdc3_session, jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        url = f"/api/v1/search/?mrn_number={number}&include_ukrdc=true"

        response = client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}


def test_search_multiple_mrn(ukrdc3_session, jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(ukrdc3_session, jtrace_session)

    # Add extra test items
    path = "/api/v1/search/?"
    for number in TEST_NUMBERS[:5]:
        path += f"mrn_number={number}&"
    path = path.rstrip("&")

    response = client.get(path)
    assert response.status_code == 200

    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {i + BUMPER + 100 for i in range(5)}


def test_search_implicit_dob(ukrdc3_session, jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(ukrdc3_session, jtrace_session)

    # Search for each item individually
    for index, _ in enumerate(TEST_NUMBERS):
        # NHS number is master record `nationalid`
        dob = f"1950-01-{str((index + 11) % 28).zfill(2)}"
        url = f"/api/v1/search/?search={dob}&include_ukrdc=true"

        response = client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + BUMPER, index + BUMPER + 100}
