from datetime import datetime

import pytest
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.exceptions import RecordTypeError
from ukrdc_fastapi.query.mirth import export

from ...utils import create_basic_facility, create_basic_patient

TEST_ID = 100000000
TEST_PID = str(TEST_ID)

# SendingFacility/SendingExtract combinations that should cause any export to fail
FAIL_SF_SE = [
    ("NHSBT", "SE"),
    ("PV", "UKRDC"),
    ("PKB", "UKRDC"),
    ("UKRR", "SE"),
    ("SF", "RADAR"),
    ("TRACING", "UKRDC"),
    ("SF", "PVMIG"),
    ("SF", "HSMIG"),
    ("SF", "SURVEY"),
]


def _commit_test_patient(ukrdc3, jtrace, sending_facility: str, sending_extract: str):
    """
    Quickly create and commit a new patientrecord with a given sending facility and extract
    """
    create_basic_facility(
        sending_facility,
        f"{sending_facility}_DESCRIPTION",
        ukrdc3,
    )
    create_basic_patient(
        TEST_ID,  # ID
        TEST_PID,  # PID
        TEST_PID,  # UKRDC
        "9434765870",  # NHS
        sending_facility,
        sending_extract,
        str(TEST_ID),
        "SURNAME_EXPORT",
        "NAME_EXPORT",
        datetime(1950, 1, 1),
        ukrdc3,
        jtrace,
    )


@pytest.mark.parametrize("sending_facility,sending_extract", FAIL_SF_SE)
async def test_export_all_to_pv_forbidden(
    ukrdc3_session,
    jtrace_session,
    redis_session,
    mirth_session,
    sending_facility,
    sending_extract,
):
    _commit_test_patient(
        ukrdc3_session, jtrace_session, sending_facility, sending_extract
    )

    with pytest.raises(RecordTypeError):
        await export.export_all_to_pv(
            ukrdc3_session.get(PatientRecord, TEST_PID),
            mirth_session,
            redis_session,
        )


@pytest.mark.parametrize("sending_facility,sending_extract", FAIL_SF_SE)
async def test_record_export_tests_forbidden(
    ukrdc3_session,
    jtrace_session,
    redis_session,
    mirth_session,
    sending_facility,
    sending_extract,
):
    _commit_test_patient(
        ukrdc3_session, jtrace_session, sending_facility, sending_extract
    )

    with pytest.raises(RecordTypeError):
        await export.export_tests_to_pv(
            ukrdc3_session.get(PatientRecord, TEST_PID),
            mirth_session,
            redis_session,
        )


@pytest.mark.parametrize("sending_facility,sending_extract", FAIL_SF_SE)
async def test_record_export_docs_forbidden(
    ukrdc3_session,
    jtrace_session,
    redis_session,
    mirth_session,
    sending_facility,
    sending_extract,
):
    _commit_test_patient(
        ukrdc3_session, jtrace_session, sending_facility, sending_extract
    )

    with pytest.raises(RecordTypeError):
        await export.export_docs_to_pv(
            ukrdc3_session.get(PatientRecord, TEST_PID),
            mirth_session,
            redis_session,
        )


@pytest.mark.parametrize("sending_facility,sending_extract", FAIL_SF_SE)
async def test_record_export_radar_forbidden(
    ukrdc3_session,
    jtrace_session,
    redis_session,
    mirth_session,
    sending_facility,
    sending_extract,
):
    _commit_test_patient(
        ukrdc3_session, jtrace_session, sending_facility, sending_extract
    )

    with pytest.raises(RecordTypeError):
        await export.export_all_to_radar(
            ukrdc3_session.get(PatientRecord, TEST_PID),
            mirth_session,
            redis_session,
        )


@pytest.mark.parametrize("sending_facility,sending_extract", FAIL_SF_SE)
async def test_record_export_pkb_forbidden(
    ukrdc3_session,
    jtrace_session,
    redis_session,
    mirth_session,
    sending_facility,
    sending_extract,
):
    _commit_test_patient(
        ukrdc3_session, jtrace_session, sending_facility, sending_extract
    )

    with pytest.raises(RecordTypeError):
        await export.export_all_to_pkb(
            ukrdc3_session.get(PatientRecord, TEST_PID),
            ukrdc3_session,
            mirth_session,
            redis_session,
        )
