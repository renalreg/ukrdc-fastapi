import sentry_sdk
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query as QueryParam
from fastapi import Security
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import PatientRecord
from ukrr_extract.config import Settings
from ukrr_extract.shared_utils import (
    ConflictingDeathTimeError,
    MissingRecordError,
    QuarterlyExtractError,
)
from ukrr_extract.rr_file import single_pid_rr_generator

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from .dependencies import _get_patientrecord

router = APIRouter()


@router.get(
    "",
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def pid_quarterly_extract(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    ukrdc3: Session = Depends(get_ukrdc3),
    quarter: int = QueryParam(...),
    centre: str = QueryParam(...),
    audit: Auditer = Depends(get_auditer),
):
    conf = Settings(
        centre=[centre],
        quarter=quarter,
    )

    try:
        results = list(
            single_pid_rr_generator(
                session=ukrdc3,
                pid=patient_record.pid,
                conf=conf,
            )
        )
    except MissingRecordError as error:
        # Expected/user-facing condition: no record found for this pid/quarter/centre
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ConflictingDeathTimeError as error:
        # Expected/user-facing condition: data conflict that needs resolving upstream
        raise HTTPException(status_code=409, detail=str(error)) from error
    except QuarterlyExtractError as error:
        # Any other known extraction error - still surface to the frontend, but
        # also report to Sentry since it's not one of the specifically
        # anticipated cases above.
        sentry_sdk.capture_exception(error)
        raise HTTPException(status_code=422, detail=str(error)) from error

    if len(results) != 1:
        # This should never happen for a single-pid extract. Report to Sentry
        # so it's visible/alertable, but don't leak internal details to the
        # frontend beyond a generic message.
        error = QuarterlyExtractError(
            f"Expected exactly one extract string for pid {patient_record.pid} "
            f"(centre={centre}, quarter={quarter}), got {len(results)}"
        )
        sentry_sdk.capture_exception(error)
        raise HTTPException(
            status_code=500,
            detail="Unexpected number of extract records generated. This has been reported.",
        ) from error

    return Response(content=results[0], media_type="text/plain")