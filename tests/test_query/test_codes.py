from ukrdc_fastapi.query import codes
from ukrdc_fastapi.schemas.code import CodeMapSchema

from ..utils import days_ago


def test_get_codes(ukrdc3_session):
    code_list = ukrdc3_session.scalars(codes.select_codes()).all()
    assert {code.code for code in code_list} == {
        "TSF01",
        "TSF02",
        "CODE_1",
        "CODE_2",
        "CODE_3",
        "G",
    }


def test_get_codes_filter_standard(ukrdc3_session):
    code_list = ukrdc3_session.scalars(
        codes.select_codes(coding_standard=["RR1+"])
    ).all()
    assert {code.code for code in code_list} == {
        "TSF01",
        "TSF02",
    }

    code_list = ukrdc3_session.scalars(
        codes.select_codes(coding_standard=["CODING_STANDARD_1", "CODING_STANDARD_2"])
    ).all()
    assert {code.code for code in code_list} == {
        "CODE_1",
        "CODE_2",
        "CODE_3",
    }


def test_get_codes_search_code(ukrdc3_session):
    code_list = ukrdc3_session.scalars(codes.select_codes(search="CODE_")).all()
    assert {code.code for code in code_list} == {
        "CODE_1",
        "CODE_2",
        "CODE_3",
    }


def test_get_codes_search_description(ukrdc3_session):
    code_list = ukrdc3_session.scalars(codes.select_codes(search="DESCRIPTION_")).all()
    assert {code.code for code in code_list} == {
        "CODE_1",
        "CODE_2",
        "CODE_3",
    }


def test_get_codes_filter_standard_and_search(ukrdc3_session):
    code_list = ukrdc3_session.scalars(
        codes.select_codes(coding_standard=["RR1+"], search="1")
    ).all()
    assert {code.code for code in code_list} == {
        "TSF01",
    }


def test_get_coding_standards(ukrdc3_session):
    standards = codes.get_coding_standards(ukrdc3_session)
    assert set(standards) == {
        "NHS_DATA_DICTIONARY",
        "CODING_STANDARD_1",
        "CODING_STANDARD_2",
        "RR1+",
    }


def test_get_code_maps(ukrdc3_session):
    code_maps = ukrdc3_session.scalars(codes.select_code_maps()).all()
    assert len(code_maps) == 2


def test_get_code_maps_filter_standard(ukrdc3_session):
    code_maps = ukrdc3_session.scalars(
        codes.select_code_maps(source_coding_standard=["CODING_STANDARD_1"])
    ).all()
    assert len(code_maps) == 1
    assert code_maps[0].source_code == "CODE_1"
    assert code_maps[0].destination_code == "CODE_2"

    code_maps = ukrdc3_session.scalars(
        codes.select_code_maps(source_coding_standard=["CODING_STANDARD_2"])
    ).all()
    assert len(code_maps) == 1
    assert code_maps[0].source_code == "CODE_2"
    assert code_maps[0].destination_code == "CODE_1"

    code_maps = ukrdc3_session.scalars(
        codes.select_code_maps(destination_coding_standard=["CODING_STANDARD_1"])
    ).all()
    assert len(code_maps) == 1
    assert code_maps[0].source_code == "CODE_2"
    assert code_maps[0].destination_code == "CODE_1"

    code_maps = ukrdc3_session.scalars(
        codes.select_code_maps(destination_coding_standard=["CODING_STANDARD_2"])
    ).all()
    assert len(code_maps) == 1
    assert code_maps[0].source_code == "CODE_1"
    assert code_maps[0].destination_code == "CODE_2"


def test_get_code_maps_filter_code(ukrdc3_session):
    code_maps = ukrdc3_session.scalars(
        codes.select_code_maps(source_code="CODE_1")
    ).all()
    assert len(code_maps) == 1
    assert code_maps[0].destination_code == "CODE_2"

    code_maps = ukrdc3_session.scalars(
        codes.select_code_maps(source_code="CODE_2")
    ).all()
    assert len(code_maps) == 1
    assert code_maps[0].destination_code == "CODE_1"

    code_maps = ukrdc3_session.scalars(
        codes.select_code_maps(destination_code="CODE_1")
    ).all()
    assert len(code_maps) == 1
    assert code_maps[0].source_code == "CODE_2"

    code_maps = ukrdc3_session.scalars(
        codes.select_code_maps(destination_code="CODE_2")
    ).all()
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
            creation_date=days_ago(365),
            update_date=None,
        )
    ]
    assert code.mapped_by == [
        CodeMapSchema(
            source_coding_standard="CODING_STANDARD_2",
            source_code="CODE_2",
            destination_coding_standard="CODING_STANDARD_1",
            destination_code="CODE_1",
            creation_date=days_ago(365),
            update_date=None,
        )
    ]


def test_get_code_exclusions(ukrdc3_session):
    exclusions = ukrdc3_session.scalars(codes.select_code_exclusions()).all()
    assert {codeexc.code for codeexc in exclusions} == {
        "CODE_1",
        "CODE_2",
        "CODE_2",
    }
    assert {codeexc.system for codeexc in exclusions} == {
        "SYSTEM_1",
        "SYSTEM_1",
        "SYSTEM_2",
    }


def test_get_code_exclusions_filter_standard(ukrdc3_session):
    exclusions = ukrdc3_session.scalars(
        codes.select_code_exclusions(coding_standard=["CODING_STANDARD_1"])
    ).all()
    assert {codeexc.code for codeexc in exclusions} == {
        "CODE_1",
    }


def test_get_code_exclusions_filter_system(ukrdc3_session):
    exclusions = ukrdc3_session.scalars(
        codes.select_code_exclusions(system=["SYSTEM_1"])
    ).all()
    assert {codeexc.code for codeexc in exclusions} == {
        "CODE_1",
        "CODE_2",
    }
