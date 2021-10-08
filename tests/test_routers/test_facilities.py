from ukrdc_sqla.ukrdc import Code

from ukrdc_fastapi.query.facilities import (
    cache_facility_error_history,
    cache_facility_statistics,
)


def test_facilities(client):
    response = client.get("/api/v1/facilities")
    ids = {item.get("id") for item in response.json()}
    assert ids == {
        "TEST_SENDING_FACILITY_1",
        "TEST_SENDING_FACILITY_2",
    }


def test_facility_detail(client, ukrdc3_session, errorsdb_session, redis_session):
    # Cache the error statistics for the facility
    test_code = Code(
        code="TEST_SENDING_FACILITY_1", description="Test sending facility 1"
    )
    cache_facility_statistics(
        test_code, ukrdc3_session, errorsdb_session, redis_session
    )

    response = client.get(f"/api/v1/facilities/{test_code.code}/")
    json = response.json()
    assert json["id"] == "TEST_SENDING_FACILITY_1"
    assert json["statistics"]["lastUpdated"]


def test_facility_error_history(client, errorsdb_session, redis_session):
    # Cache the error history for the facility
    test_code = Code(
        code="TEST_SENDING_FACILITY_1", description="Test sending facility 1"
    )
    cache_facility_error_history(test_code, errorsdb_session, redis_session)

    response = client.get(f"/api/v1/facilities/{test_code.code}/error_history/")
    json = response.json()
    assert len(json) == 1
    assert json[0].get("time") == "2021-01-01"
