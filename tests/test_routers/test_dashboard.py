def test_dashboard(client, redis_session):
    response = client.get("/api/v1/dash")
    print(response.text)
    assert response.status_code == 200
    assert redis_session.exists("dashboard:workitems")
    assert redis_session.exists("dashboard:ukrdcrecords")

    cached_response = client.get("/api/v1/dash")
    assert cached_response.json() == response.json()


def test_dashboard_cache(client, redis_session):
    redis_session.hset(
        "dashboard:workitems", mapping={"total": 11, "day": 11, "prev": 11}
    )
    redis_session.hset(
        "dashboard:ukrdcrecords", mapping={"total": 22, "day": 22, "prev": 22}
    )
    response = client.get("/api/v1/dash")
    assert response.status_code == 200
    assert response.json()["workitems"] == {
        "total": 11,
        "day": 11,
        "prev": 11,
        "href": "/api/v1/workitems/",
    }
    assert response.json()["ukrdcrecords"] == {
        "total": 22,
        "day": 22,
        "prev": 22,
        "href": "/api/v1/masterrecords/",
    }
