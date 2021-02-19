def test_workitems_list(client):
    response = client.get("/workitems")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": 1,
            "person_id": 3,
            "master_id": 1,
            "type": 9,
            "description": "DESCRIPTION_1",
            "status": 1,
            "last_updated": "2020-03-16T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
        {
            "id": 2,
            "person_id": 4,
            "master_id": 1,
            "type": 9,
            "description": "DESCRIPTION_2",
            "status": 1,
            "last_updated": "2021-01-01T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
        {
            "id": 3,
            "person_id": 4,
            "master_id": 2,
            "type": 9,
            "description": "DESCRIPTION_3",
            "status": 1,
            "last_updated": "2021-01-01T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
    ]


def test_workitems_list_ukrdcid_filter_single(client):
    response = client.get("/workitems?ukrdcid=999999999")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": 1,
            "person_id": 3,
            "master_id": 1,
            "type": 9,
            "description": "DESCRIPTION_1",
            "status": 1,
            "last_updated": "2020-03-16T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
        {
            "id": 2,
            "person_id": 4,
            "master_id": 1,
            "type": 9,
            "description": "DESCRIPTION_2",
            "status": 1,
            "last_updated": "2021-01-01T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
    ]


def test_workitems_list_ukrdcid_filter_multiple(client):
    response = client.get("/workitems?ukrdcid=999999999&ukrdcid=999999911")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": 1,
            "person_id": 3,
            "master_id": 1,
            "type": 9,
            "description": "DESCRIPTION_1",
            "status": 1,
            "last_updated": "2020-03-16T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
        {
            "id": 2,
            "person_id": 4,
            "master_id": 1,
            "type": 9,
            "description": "DESCRIPTION_2",
            "status": 1,
            "last_updated": "2021-01-01T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
        {
            "id": 3,
            "person_id": 4,
            "master_id": 2,
            "type": 9,
            "description": "DESCRIPTION_3",
            "status": 1,
            "last_updated": "2021-01-01T00:00:00",
            "updated_by": None,
            "update_description": None,
            "attributes": None,
        },
    ]


def test_workitems_detail(client):
    response = client.get("/workitems/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "person_id": 3,
        "master_id": 1,
        "type": 9,
        "description": "DESCRIPTION_1",
        "status": 1,
        "last_updated": "2020-03-16T00:00:00",
        "updated_by": None,
        "update_description": None,
        "attributes": None,
        "person": {
            "id": 3,
            "originator": "UKRDC",
            "localid": "192837465",
            "localid_type": "CLPID",
            "date_of_birth": "1950-01-01",
            "gender": "9",
            "date_of_death": None,
            "givenname": None,
            "surname": None,
            "xref_entries": [],
        },
        "master_record": {
            "id": 1,
            "last_updated": "2020-03-16T00:00:00",
            "date_of_birth": "1950-01-01",
            "gender": None,
            "givenname": None,
            "surname": None,
            "nationalid": "999999999",
            "nationalid_type": "UKRDC",
            "status": 0,
            "effective_date": "2020-03-16T00:00:00",
        },
        "related": [
            {
                "id": 2,
                "person_id": 4,
                "master_id": 1,
            }
        ],
    }


def test_workitems_detail_not_found(client):
    response = client.get("/workitems/9999")
    assert response.status_code == 404
