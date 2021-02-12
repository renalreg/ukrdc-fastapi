def test_record(client):
    response = client.get("/viewer/record/PYTEST01:PV:00000000A")
    assert response.status_code == 200
    # print(response.json())
