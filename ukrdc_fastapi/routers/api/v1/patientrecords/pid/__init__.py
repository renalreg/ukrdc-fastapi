import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam
from fastapi import Security
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import Observation, ResultItem

from ukrdc_fastapi.dependencies import get_jtrace, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.laborders import get_laborders
from ukrdc_fastapi.query.medications import get_medications
from ukrdc_fastapi.query.observations import get_observation_codes, get_observations
from ukrdc_fastapi.query.patientrecords import (
    get_patientrecord,
    get_patientrecords_related_to_patientrecord,
)
from ukrdc_fastapi.query.resultitems import get_resultitem_services, get_resultitems
from ukrdc_fastapi.query.surveys import get_surveys
from ukrdc_fastapi.schemas.laborder import (
    LabOrderShortSchema,
    ResultItemSchema,
    ResultItemServiceSchema,
)
from ukrdc_fastapi.schemas.medication import MedicationSchema
from ukrdc_fastapi.schemas.observation import ObservationSchema
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSchema
from ukrdc_fastapi.schemas.survey import SurveySchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import Sorter, make_sorter

from . import export

router = APIRouter(prefix="/{pid}")
router.include_router(export.router, prefix="/export")


@router.get(
    "/",
    response_model=PatientRecordSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_record(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a specific patient record"""
    return get_patientrecord(ukrdc3, pid, user)


@router.get(
    "/related/",
    response_model=list[PatientRecordSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_related(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive patient records related to a specific patient record"""
    return get_patientrecords_related_to_patientrecord(ukrdc3, jtrace, pid, user).all()


@router.get(
    "/laborders/",
    response_model=Page[LabOrderShortSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_laborders(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a specific patient's lab orders"""
    return paginate(get_laborders(ukrdc3, user, pid=pid))


@router.get(
    "/resultitems/",
    response_model=Page[ResultItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_resultitems(
    pid: str,
    service_id: Optional[list[str]] = QueryParam([]),
    order_id: Optional[list[str]] = QueryParam([]),
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
    sorter: Sorter = Depends(
        make_sorter(
            [ResultItem.observation_time, ResultItem.entered_on],
            default_sort_by=ResultItem.observation_time,
        )
    ),
):
    """Retreive a specific patient's lab orders"""

    query = get_resultitems(
        ukrdc3,
        user,
        pid=pid,
        service_id=service_id,
        order_id=order_id,
        since=since,
        until=until,
    )
    return paginate(sorter.sort(query))


@router.get(
    "/resultitems/services",
    response_model=list[ResultItemServiceSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_resultitems_services(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of resultitem services available for a specific patient"""
    return get_resultitem_services(ukrdc3, user, pid=pid)


@router.get(
    "/observations/",
    response_model=Page[ObservationSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_observations(
    pid: str,
    code: Optional[list[str]] = QueryParam([]),
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
    sorter: Sorter = Depends(
        make_sorter(
            [Observation.observation_time, Observation.updated_on],
            default_sort_by=Observation.observation_time,
        )
    ),
):
    """Retreive a specific patient's lab orders"""
    query = get_observations(ukrdc3, user, pid=pid, codes=code)
    return paginate(sorter.sort(query))


@router.get(
    "/observations/codes",
    response_model=list[str],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_observations_codes(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of observation codes available for a specific patient"""
    return get_observation_codes(ukrdc3, user, pid=pid)


@router.get(
    "/medications/",
    response_model=list[MedicationSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_medications(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a specific patient's medications"""
    return get_medications(ukrdc3, user, pid=pid).all()


@router.get(
    "/surveys/",
    response_model=list[SurveySchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_surveys(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a specific patient's surveys"""
    return get_surveys(ukrdc3, user, pid=pid).all()
