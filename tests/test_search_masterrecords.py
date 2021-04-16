from datetime import datetime

from stdnum.gb import nhs
from ukrdc_sqla.empi import MasterRecord

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


def _commit_extra_patients(session, number_type="NHS"):
    for index, number in enumerate(TEST_NUMBERS):
        master_record = MasterRecord(
            id=index + 99,
            status=0,
            last_updated=datetime(2020, 3, (index + 11) % 28),
            date_of_birth=datetime(1950, 1, (index + 11) % 28),
            nationalid=number,
            nationalid_type=number_type,
            effective_date=datetime(2020, 3, 16),
        )
        session.add(master_record)
        session.commit()


def test_search_all(jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(jtrace_session, number_type="NHS")

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        url = f"/api/empi/search/masterrecords?search={number}"

        response = client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + 99}


def test_search_nhsno(jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(jtrace_session, number_type="NHS")

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        url = f"/api/empi/search/masterrecords?nhs_number={number}"

        response = client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + 99}


def test_search_multiple_nhsno(jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(jtrace_session, number_type="NHS")

    # Add extra test items
    path = "/api/empi/search/masterrecords?"
    for number in TEST_NUMBERS[:5]:
        path += f"nhs_number={number}&"
    path = path.rstrip("&")

    response = client.get(path)
    assert response.status_code == 200

    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {i + 99 for i in range(5)}


def test_search_implicit_dob(jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(jtrace_session, number_type="NHS")

    # Search for each item individually
    for index, _ in enumerate(TEST_NUMBERS):
        # NHS number is master record `nationalid`
        dob = f"1950-01-{str((index + 11) % 28).zfill(2)}"
        url = f"/api/empi/search/masterrecords?search={dob}"

        response = client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + 99}
