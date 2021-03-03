from datetime import datetime

from ukrdc_fastapi.models.empi import LinkRecord, MasterRecord, Person


def _commit_extra_patients(session, n, number_type="NHS"):
    master_record = MasterRecord(
        id=n,
        status=0,
        last_updated=datetime(2020, 3, n % 28),
        date_of_birth=datetime(1950, 1, n % 28),
        nationalid=f"{n}".zfill(9)[::-1],
        nationalid_type=number_type,
        effective_date=datetime(2020, 3, 16),
    )
    person = Person(
        id=n,
        originator="UKRDC",
        localid=f"{n}".zfill(9),
        localid_type="CLPID",
        date_of_birth=datetime(1950, 1, n % 28),
        gender="9",
    )
    link_record = LinkRecord(
        id=n,
        person_id=n,
        master_id=n,
        link_type=0,
        link_code=0,
        last_updated=datetime(2019, 1, n % 28),
    )
    session.add(master_record)
    session.add(person)
    session.add(link_record)
    session.commit()


def test_search_nhsno(jtrace_session, client):
    test_range = range(10, 20)

    # Add extra test items
    for i in test_range:
        _commit_extra_patients(jtrace_session, i, number_type="NHS")

    # Search for each item individually
    for i in test_range:
        # NHS number is master record `nationalid`
        nhs_number = f"{i}".zfill(9)[::-1]
        url = f"/empi/search/person?nhs_number={nhs_number}"

        response = client.get(url)
        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.json()["items"]}
        assert returned_ids == {i}


def test_search_multiple_nhsno(jtrace_session, client):
    test_range = range(10, 20)
    search_range = range(10, 12)

    # Add extra test items
    for i in test_range:
        _commit_extra_patients(jtrace_session, i, number_type="NHS")

    # Add extra test items
    path = "/empi/search/person?"
    for i in search_range:
        # NHS number is master record `nationalid`
        nhs_number = f"{i}".zfill(9)[::-1]
        path += f"nhs_number={nhs_number}&"
    path = path.rstrip("&")

    response = client.get(path)
    assert response.status_code == 200

    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {10, 11}
