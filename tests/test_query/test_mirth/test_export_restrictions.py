from datetime import datetime

import pytest

from ukrdc_fastapi.exceptions import RecordTypeError
from ukrdc_fastapi.query.mirth import export

from ...utils import create_basic_facility, create_basic_patient

TEST_ID = 100000000


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
        str(TEST_ID),  # PID
        str(TEST_ID),  # UKRDC
        "9434765870",  # NHS
        sending_facility,
        sending_extract,
        f"PYTEST:EXPORT:{TEST_ID}",
        "SURNAME_EXPORT",
        "NAME_EXPORT",
        datetime(1950, 1, 1),
        ukrdc3,
        jtrace,
    )


@pytest.mark.parametrize(
    "sending_facility,sending_extract",
    [
        ("NHSBT", "SENDING_EXTRACT"),
        ("PV", "UKRDC"),
        ("PKB", "UKRDC"),
        ("UKRR", "SENDING_EXTRACT"),
        ("SENDING_FACILITY", "RADAR"),
        ("TRACING", "UKRDC"),
        ("SENDING_FACILITY", "PVMIG"),
        ("SENDING_FACILITY", "HSMIG"),
        ("SENDING_FACILITY", "SURVEY"),
    ],
)
async def test_export_all_to_pv_forbidden(
    ukrdc3_session,
    jtrace_session,
    redis_session,
    mirth_session,
    superuser,
    sending_facility,
    sending_extract,
):
    _commit_test_patient(
        ukrdc3_session, jtrace_session, sending_facility, sending_extract
    )

    with pytest.raises(RecordTypeError):
        await export.export_all_to_pv(
            str(TEST_ID), superuser, ukrdc3_session, mirth_session, redis_session
        )
