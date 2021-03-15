from datetime import datetime

from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person

from ukrdc_fastapi.schemas.empi import LinkRecordSchema


def test_linkrecords_list(client):
    response = client.get("/api/empi/linkrecords")
    assert response.status_code == 200

    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1, 2}

    for item in response.json()["items"]:
        assert LinkRecordSchema(**item)


def test_linkrecords_complex_chain(client, jtrace_session):
    common_m_props = {
        "status": 0,
        "last_updated": datetime(2020, 3, 16),
        "date_of_birth": datetime(1950, 1, 1),
        "nationalid_type": "UKRDC",
        "effective_date": datetime(2020, 3, 16),
    }
    common_p_props = {
        "originator": "UKRDC",
        "localid_type": "CLPID",
        "date_of_birth": datetime(1950, 1, 1),
        "gender": "9",
        "localid": "XXX",
    }
    common_l_props = {
        "link_type": 0,
        "link_code": 0,
        "last_updated": datetime(2019, 1, 1),
    }

    # Create 4 nontrivially related linkrecords
    m1 = MasterRecord(id=101, nationalid="101", **common_m_props)
    l1 = LinkRecord(id=101, person_id=101, master_id=101, **common_l_props)
    p1 = Person(id=101, **common_p_props)
    l2 = LinkRecord(id=102, person_id=101, master_id=102, **common_l_props)
    m2 = MasterRecord(id=102, nationalid="102", **common_m_props)
    l3 = LinkRecord(id=103, person_id=102, master_id=102, **common_l_props)
    p2 = Person(id=102, **common_p_props)
    l4 = LinkRecord(id=104, person_id=102, master_id=103, **common_l_props)
    m3 = MasterRecord(id=103, nationalid="103", **common_m_props)

    # Create one unrelated link record
    m1b = MasterRecord(id=201, nationalid="201", **common_m_props)
    l1b = LinkRecord(id=201, person_id=201, master_id=201, **common_l_props)
    p1b = Person(id=201, **common_p_props)

    jtrace_session.bulk_save_objects(
        [m1, l1, p1, l2, m2, l3, p2, l4, m3, m1b, l1b, p1b]
    )
    jtrace_session.commit()

    # Test the complex chain

    response = client.get("/api/empi/linkrecords?ni=101")
    assert response.status_code == 200
    # Get a list of all returned LinkRecord IDs
    returned_linkrecord_ids = [item.get("id") for item in response.json()["items"]]
    # We expect only the 4 related LinkRecords
    assert returned_linkrecord_ids == [101, 102, 103, 104]

    # Test the simple chain

    response = client.get("/api/empi/linkrecords?ni=201")
    assert response.status_code == 200
    # Get a list of all returned LinkRecord IDs
    returned_linkrecord_ids = [item.get("id") for item in response.json()["items"]]
    # We expect only the 4 related LinkRecords
    assert returned_linkrecord_ids == [201]
