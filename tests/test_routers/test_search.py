from datetime import date, datetime

from stdnum.gb import nhs
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person, PidXRef

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
        dob = datetime(1950, 1, (index + 11) % 28)
        localid = f"PYTEST:SEARCH:{number}"
        master_record = MasterRecord(
            id=index + 99,
            status=0,
            last_updated=dob,
            date_of_birth=dob,
            nationalid=number,
            nationalid_type=number_type,
            effective_date=datetime(2020, 3, 16),
        )
        person = Person(
            id=index + 99,
            originator="UKRDC",
            localid=localid,
            localid_type="CLPID",
            date_of_birth=dob,
            gender="9",
        )
        link_record = LinkRecord(
            id=index + 99,
            person_id=index + 99,
            master_id=index + 99,
            link_type=0,
            link_code=0,
            last_updated=datetime(2019, 1, 1),
        )
        xref = PidXRef(
            id=index + 99,
            pid=localid,
            sending_facility="TEST_SENDING_FACILITY_1",
            sending_extract="XREF_SENDING_EXTRACT_1",
            localid=number,
        )
        session.add(master_record)
        session.add(person)
        session.add(link_record)
        session.add(xref)
        session.commit()


def test_search_all(jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(jtrace_session, number_type="NHS")

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        url = f"/api/v1/search/?search={number}"

        response = client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + 99}


def test_search_mrn(jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(jtrace_session, number_type="NHS")

    # Search for each item individually
    for index, number in enumerate(TEST_NUMBERS):
        url = f"/api/v1/search/?mrn_number={number}"

        response = client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + 99}


def test_search_multiple_mrn(jtrace_session, client):
    # Add extra test items
    _commit_extra_patients(jtrace_session, number_type="NHS")

    # Add extra test items
    path = "/api/v1/search/?"
    for number in TEST_NUMBERS[:5]:
        path += f"mrn_number={number}&"
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
        url = f"/api/v1/search/?search={dob}"

        response = client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {index + 99}
