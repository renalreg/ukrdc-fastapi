def test_facilities(client):
    response = client.get("/api/v1/facilities")
    ids = {item.get("id") for item in response.json()}
    assert ids == {
        "TEST_SENDING_FACILITY_1",
        "TEST_SENDING_FACILITY_2",
    }


def test_facility_detail(client):
    response = client.get("/api/v1/facilities/TEST_SENDING_FACILITY_1")
    json = response.json()
    assert json["id"] == "TEST_SENDING_FACILITY_1"
    # Expect non-null values
    assert json["statistics"]["recordsWithErrors"] == 1


def test_facility_error_history(client):
    response = client.get("/api/v1/facilities/TEST_SENDING_FACILITY_1/error_history")
    json = response.json()
    len(json) == 1
    assert json[0].get("time") == "2021-01-01"
