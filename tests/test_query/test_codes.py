import datetime

from fastapi.exceptions import HTTPException

from ukrdc_fastapi.query import codes
from ukrdc_fastapi.schemas.code import CodeMapSchema


def test_get_codes(ukrdc3_session):
    code_list = codes.get_codes(ukrdc3_session).all()
    assert {code.code for code in code_list} == {
        "TEST_SENDING_FACILITY_1",
        "TEST_SENDING_FACILITY_2",
        "CODE_1",
        "CODE_2",
    }


def test_get_codes_filter_standard(ukrdc3_session):
    code_list = codes.get_codes(ukrdc3_session, coding_standard=["RR1+"]).all()
    assert {code.code for code in code_list} == {
        "TEST_SENDING_FACILITY_1",
        "TEST_SENDING_FACILITY_2",
    }

    code_list = codes.get_codes(
        ukrdc3_session, coding_standard=["CODING_STANDARD_1", "CODING_STANDARD_2"]
    ).all()
    assert {code.code for code in code_list} == {
        "CODE_1",
        "CODE_2",
    }


def test_get_coding_standards(ukrdc3_session):
    standards = codes.get_coding_standards(ukrdc3_session)
    assert standards == ["CODING_STANDARD_1", "CODING_STANDARD_2", "RR1+"]


def test_get_code_maps(ukrdc3_session):
    code_maps = codes.get_code_maps(ukrdc3_session).all()
    assert len(code_maps) == 2


def test_get_code_maps_filter_standard(ukrdc3_session):
    code_maps = codes.get_code_maps(
        ukrdc3_session, source_coding_standard=["CODING_STANDARD_1"]
    ).all()
    assert len(code_maps) == 1
    assert code_maps[0].source_code == "CODE_1"
    assert code_maps[0].destination_code == "CODE_2"

    code_maps = codes.get_code_maps(
        ukrdc3_session, source_coding_standard=["CODING_STANDARD_2"]
    ).all()
    assert len(code_maps) == 1
    assert code_maps[0].source_code == "CODE_2"
    assert code_maps[0].destination_code == "CODE_1"

    code_maps = codes.get_code_maps(
        ukrdc3_session, destination_coding_standard=["CODING_STANDARD_1"]
    ).all()
    assert len(code_maps) == 1
    assert code_maps[0].source_code == "CODE_2"
    assert code_maps[0].destination_code == "CODE_1"

    code_maps = codes.get_code_maps(
        ukrdc3_session, destination_coding_standard=["CODING_STANDARD_2"]
    ).all()
    assert len(code_maps) == 1
    assert code_maps[0].source_code == "CODE_1"
    assert code_maps[0].destination_code == "CODE_2"


def test_get_code_maps_filter_code(ukrdc3_session):
    code_maps = codes.get_code_maps(ukrdc3_session, source_code="CODE_1").all()
    assert len(code_maps) == 1
    assert code_maps[0].destination_code == "CODE_2"

    code_maps = codes.get_code_maps(ukrdc3_session, source_code="CODE_2").all()
    assert len(code_maps) == 1
    assert code_maps[0].destination_code == "CODE_1"

    code_maps = codes.get_code_maps(ukrdc3_session, destination_code="CODE_1").all()
    assert len(code_maps) == 1
    assert code_maps[0].source_code == "CODE_2"

    code_maps = codes.get_code_maps(ukrdc3_session, destination_code="CODE_2").all()
    assert len(code_maps) == 1
    assert code_maps[0].source_code == "CODE_1"


def test_get_code(ukrdc3_session):
    code = codes.get_code(ukrdc3_session, "CODING_STANDARD_1", "CODE_1")
    assert code
    assert code.maps_to == [
        CodeMapSchema(
            source_coding_standard="CODING_STANDARD_1",
            source_code="CODE_1",
            destination_coding_standard="CODING_STANDARD_2",
            destination_code="CODE_2",
            creation_date=datetime.datetime(2020, 3, 16, 0, 0),
            update_date=None,
        )
    ]
    assert code.mapped_by == [
        CodeMapSchema(
            source_coding_standard="CODING_STANDARD_2",
            source_code="CODE_2",
            destination_coding_standard="CODING_STANDARD_1",
            destination_code="CODE_1",
            creation_date=datetime.datetime(2020, 3, 16, 0, 0),
            update_date=None,
        )
    ]