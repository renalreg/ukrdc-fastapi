from uuid import UUID

from ukrdc_fastapi.utils.mirth import ChannelFullModel, ChannelGroup


def test_channels_list(client, httpx_session):
    response = client.get("/api/mirth/channels/")
    assert response.status_code == 200
    channels = [ChannelFullModel(**item) for item in response.json()]
    assert len(channels) > 0


def test_channels_groups(client, httpx_session):
    response = client.get("/api/mirth/groups/")
    assert response.status_code == 200
    groups = [ChannelGroup(**item) for item in response.json()]
    assert len(groups) > 0


def test_channels_detail(client, httpx_session):
    response = client.get("/api/mirth/channels/57f40021-e05e-4308-98ef-8509c2f9d766/")
    assert response.status_code == 200
    channel = ChannelFullModel(**response.json())
    assert channel.id == UUID("57f40021-e05e-4308-98ef-8509c2f9d766")
