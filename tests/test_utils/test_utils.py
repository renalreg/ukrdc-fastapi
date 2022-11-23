import pytest
from ukrdc_sqla.ukrdc import PatientRecord

from tests.conftest import PID_1, PID_2, PID_3, UKRDCID_1, UKRDCID_2
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


def test_query_union_one(ukrdc3_session):
    q1 = ukrdc3_session.query(PatientRecord).filter(PatientRecord.pid == PID_1)

    u = utils.query_union([q1])
    assert {record.pid for record in u} == {PID_1}


def test_query_union_multiple(ukrdc3_session):
    pids_to_test = {PID_1, PID_2, PID_3}
    qs = [
        ukrdc3_session.query(PatientRecord).filter(PatientRecord.pid == test_pid)
        for test_pid in pids_to_test
    ]

    u = utils.query_union(qs)
    assert {record.pid for record in u} == pids_to_test


def test_query_union_multiple_overlapping(ukrdc3_session):
    pids_to_test = {PID_1, PID_2, PID_3}
    ukrdcids_to_test = {UKRDCID_1, UKRDCID_2}
    qs = [
        ukrdc3_session.query(PatientRecord).filter(PatientRecord.pid == test_pid)
        for test_pid in pids_to_test
    ]

    qs.extend(
        [
            ukrdc3_session.query(PatientRecord).filter(
                PatientRecord.ukrdcid == test_ukrdcid
            )
            for test_ukrdcid in ukrdcids_to_test
        ]
    )

    u = utils.query_union(qs)
    assert {record.pid for record in u} == pids_to_test


def test_query_union_none():
    with pytest.raises(ValueError):
        utils.query_union([])
