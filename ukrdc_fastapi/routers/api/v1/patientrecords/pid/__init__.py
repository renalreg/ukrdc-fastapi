import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query as QueryParam
from fastapi import Security
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import LabOrder, Observation, PVDelete, ResultItem

from ukrdc_fastapi.dependencies import get_jtrace, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.delete import delete_pid, summarise_delete_pid
from ukrdc_fastapi.query.patientrecords import (
    get_patientrecord,
    get_patientrecords_related_to_patientrecord,
)
from ukrdc_fastapi.schemas.delete import DeletePIDRequestSchema
from ukrdc_fastapi.schemas.laborder import (
    LabOrderSchema,
    LabOrderShortSchema,
    ResultItemSchema,
    ResultItemServiceSchema,
)
from ukrdc_fastapi.schemas.medication import MedicationSchema
from ukrdc_fastapi.schemas.observation import ObservationSchema
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSchema
from ukrdc_fastapi.schemas.survey import SurveySchema
from ukrdc_fastapi.schemas.treatment import TreatmentSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import Sorter, make_sorter

from . import export

router = APIRouter(prefix="/{pid}")
router.include_router(export.router, prefix="/export")

# Self-resources


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


@router.post(
    "/delete",
    dependencies=[
        Security(
            auth.permission([Permissions.READ_RECORDS, Permissions.DELETE_RECORDS])
        )
    ],
)
def patient_delete(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
    jtrace: Session = Depends(get_jtrace),
    args: Optional[DeletePIDRequestSchema] = None,
):
    """Delete a specific patient record and all its associated data"""
    if args and args.hash:
        return delete_pid(ukrdc3, jtrace, pid, args.hash, user)
    return summarise_delete_pid(ukrdc3, jtrace, pid, user)


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


# Internal resources


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
    observations = get_patientrecord(ukrdc3, pid, user).observations
    if code:
        observations = observations.filter(Observation.observation_code.in_(code))
    return paginate(sorter.sort(observations))


@router.get(
    "/observation_codes",
    response_model=list[str],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_observations_codes(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of observation codes available for a specific patient"""
    observations = get_patientrecord(ukrdc3, pid, user).observations
    codes = observations.distinct(Observation.observation_code)
    return {item.observation_code for item in codes.all()}


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
    record = get_patientrecord(ukrdc3, pid, user)
    return record.medications.all()


@router.get(
    "/treatments/",
    response_model=list[TreatmentSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_treatments(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a specific patient's treatments"""
    record = get_patientrecord(ukrdc3, pid, user)
    return record.treatments.all()


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
    record = get_patientrecord(ukrdc3, pid, user)
    return record.surveys.all()


# External resources


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
    return paginate(get_patientrecord(ukrdc3, pid, user).lab_orders)


@router.get(
    "/laborders/{order_id}/",
    response_model=LabOrderSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def laborder_get(
    pid: str,
    order_id: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
) -> LabOrder:
    """Retreive a particular lab order"""
    order = (
        get_patientrecord(ukrdc3, pid, user)
        .lab_orders.filter(LabOrder.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(404, detail="Lab Order not found")
    return order


@router.delete(
    "/laborders/{order_id}/",
    status_code=204,
    dependencies=[Security(auth.permission(Permissions.WRITE_RECORDS))],
)
def laborder_delete(
    pid: str,
    order_id: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
) -> None:
    """Mark a particular lab order for deletion"""
    order = (
        get_patientrecord(ukrdc3, pid, user)
        .lab_orders.filter(LabOrder.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(404, detail="Lab Order not found")

    deletes = [
        PVDelete(
            pid=pid,
            observation_time=item.observation_time,
            service_id=item.service_id,
        )
        for item in order.result_items
    ]
    ukrdc3.bulk_save_objects(deletes)

    ukrdc3.delete(order)
    ukrdc3.commit()


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

    query = get_patientrecord(ukrdc3, pid, user).result_items

    if service_id:
        query = query.filter(ResultItem.service_id.in_(service_id))
    if order_id:
        query = query.filter(ResultItem.order_id.in_(order_id))
    if since:
        query = query.filter(ResultItem.observation_time >= since)
    if until:
        query = query.filter(ResultItem.observation_time <= until)

    return paginate(sorter.sort(query))


@router.get(
    "/resultitems/{resultitem_id}/",
    response_model=ResultItemSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def resultitem_detail(
    pid: str,
    resultitem_id: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
) -> ResultItem:
    """Retreive a particular lab result"""
    item = (
        get_patientrecord(ukrdc3, pid, user)
        .result_items.filter(ResultItem.id == resultitem_id)
        .first()
    )
    if not item:
        raise HTTPException(404, detail="Result item not found")
    return item


@router.delete(
    "/resultitems/{resultitem_id}/",
    status_code=204,
    dependencies=[Security(auth.permission(Permissions.WRITE_RECORDS))],
)
def resultitem_delete(
    pid: str,
    resultitem_id: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
) -> None:
    """Mark a particular lab result for deletion"""
    item = (
        get_patientrecord(ukrdc3, pid, user)
        .result_items.filter(ResultItem.id == resultitem_id)
        .first()
    )
    if not item:
        raise HTTPException(404, detail="Result item not found")

    order: Optional[LabOrder] = item.order

    ukrdc3.delete(item)
    ukrdc3.commit()

    if order and order.result_items.count() == 0:
        ukrdc3.delete(order)
    ukrdc3.commit()


@router.get(
    "/resultitem_services",
    response_model=list[ResultItemServiceSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_resultitems_services(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of resultitem services available for a specific patient"""
    items = get_patientrecord(ukrdc3, pid, user).result_items
    services = items.distinct(ResultItem.service_id)
    return [
        ResultItemServiceSchema(
            id=item.service_id,
            description=item.service_id_description,
            standard=item.service_id_std,
        )
        for item in services.all()
    ]
