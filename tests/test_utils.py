import requests_mock

from ukrdc_fastapi import utils
from ukrdc_fastapi.config import settings


def test_build_db_uri_general():
    assert (
        utils.build_db_uri("postgres", "host", 5432, "user", "pass", "dbname")
        == "postgres://user:pass@host:5432/dbname"
    )


def test_build_db_uri_sqlite():
    assert (
        utils.build_db_uri("sqlite", "host", 5432, "user", "pass", "dbname")
        == "sqlite:///dbname"
    )


def test_post_mirth_message(requests_session):
    settings.mirth_url = "mock://mirth.url"
    with requests_session:
        response = utils.post_mirth_message("/mirth/path/", message="MESSAGE")
        assert response.request.scheme == "mock"
        assert response.request.hostname == "mirth.url"
        assert response.request.path == "/mirth/path/"
        assert response.text == "MESSAGE"


def test_post_mirth_message_and_catch_nopost():
    response = utils.post_mirth_message_and_catch(
        "/mirth/path/", message="MESSAGE", post=False
    )
    assert response == {"status": "ignored", "message": "MESSAGE"}


def test_post_mirth_message_and_catch(requests_session):
    settings.mirth_url = "mock://mirth.url"
    with requests_session:
        response = utils.post_mirth_message_and_catch("/mirth/path/", message="MESSAGE")
        assert response == {"status": "success", "message": "MESSAGE"}
