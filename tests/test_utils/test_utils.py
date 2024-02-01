from ukrdc_fastapi import utils


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

