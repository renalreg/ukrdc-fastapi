import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query as QueryParam
from fastapi import Security
from fastapi.responses import Response
from sqlalchemy.orm import Session, defer
from ukrdc_sqla.ukrdc import (
    Document,
    LabOrder,
    Observation,
    PatientRecord,
    PVDelete,
    ResultItem,
)

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
from ukrdc_fastapi.schemas.patientrecord import (
    DocumentSchema,
    DocumentSummarySchema,
    PatientRecordSchema,
)
from ukrdc_fastapi.schemas.survey import SurveySchema
from ukrdc_fastapi.schemas.treatment import TreatmentSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import Sorter, make_sorter

from . import export

router = APIRouter(prefix="/{pid}")
router.include_router(export.router, prefix="/export")


def _get_patientrecord(
    pid: str,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
) -> PatientRecord:
    """Simple dependency to turn pid query param and User object into a PatientRecord object."""
    return get_patientrecord(ukrdc3, pid, user)


# Self-resources


@router.get(
    "/",
    response_model=PatientRecordSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_get(patient_record: PatientRecord = Depends(_get_patientrecord)):
    """Retreive a specific patient record"""
    return patient_record


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
    user: UKRDCUser = Security(auth.get_user()),
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
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive patient records related to a specific patient record"""
    return get_patientrecords_related_to_patientrecord(ukrdc3, jtrace, pid, user).all()


# Internal resources


@router.get(
    "/medications/",
    response_model=list[MedicationSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_medications(patient_record: PatientRecord = Depends(_get_patientrecord)):
    """Retreive a specific patient's medications"""
    return patient_record.medications.all()


@router.get(
    "/treatments/",
    response_model=list[TreatmentSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_treatments(patient_record: PatientRecord = Depends(_get_patientrecord)):
    """Retreive a specific patient's treatments"""
    return patient_record.treatments.all()


@router.get(
    "/surveys/",
    response_model=list[SurveySchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_surveys(patient_record: PatientRecord = Depends(_get_patientrecord)):
    """Retreive a specific patient's surveys"""
    return patient_record.surveys.all()


@router.get(
    "/documents/",
    response_model=Page[DocumentSummarySchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_documents(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    sorter: Sorter = Depends(
        make_sorter(
            [Document.documenttime, Document.updatedon],
            default_sort_by=Document.documenttime,
        )
    ),
):
    """Retreive a specific patient's documents"""
    # NOTE: We defer the 'stream' column to avoid sending the full PDF file content
    # when we're just querying the list of documents.
    return paginate(sorter.sort(patient_record.documents.options(defer("stream"))))


@router.get(
    "/documents/{document_id}/",
    response_model=DocumentSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def document_get(
    document_id: str, patient_record: PatientRecord = Depends(_get_patientrecord)
):
    """Retreive a specific patient's document information"""
    document = patient_record.documents.filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(404, detail="Document not found")
    return document


@router.get(
    "/documents/{document_id}/download",
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def document_download(
    document_id: str, patient_record: PatientRecord = Depends(_get_patientrecord)
):
    """Retreive a specific patient's document file"""
    document: Optional[Document] = patient_record.documents.filter(
        Document.id == document_id
    ).first()
    if not document:
        raise HTTPException(404, detail="Document not found")

    media_type: str
    stream: bytes
    filename: str
    if not document.filetype:
        media_type = "text/csv"
        stream = document.notetext.encode()
        filename = f"{document.documentname}.txt"
    else:
        media_type = document.filetype
        stream = document.stream
        filename = document.filename

    response = Response(content=stream, media_type=media_type)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


# Complex internal resources


@router.get(
    "/observations/",
    response_model=Page[ObservationSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_observations(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    code: Optional[list[str]] = QueryParam([]),
    sorter: Sorter = Depends(
        make_sorter(
            [Observation.observation_time, Observation.updated_on],
            default_sort_by=Observation.observation_time,
        )
    ),
):
    """Retreive a specific patient's lab orders"""
    observations = patient_record.observations
    if code:
        observations = observations.filter(Observation.observation_code.in_(code))
    return paginate(sorter.sort(observations))


@router.get(
    "/observation_codes",
    response_model=list[str],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_observation_codes(
    patient_record: PatientRecord = Depends(_get_patientrecord),
):
    """Retreive a list of observation codes available for a specific patient"""
    codes = patient_record.observations.distinct(Observation.observation_code)
    return {item.observation_code for item in codes.all()}


@router.get(
    "/laborders/",
    response_model=Page[LabOrderShortSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_laborders(patient_record: PatientRecord = Depends(_get_patientrecord)):
    """Retreive a specific patient's lab orders"""
    return paginate(
        patient_record.lab_orders.order_by(LabOrder.specimen_collected_time.desc())
    )


@router.get(
    "/laborders/{order_id}/",
    response_model=LabOrderSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def laborder_get(
    order_id: str, patient_record: PatientRecord = Depends(_get_patientrecord)
) -> LabOrder:
    """Retreive a particular lab order"""
    order = patient_record.lab_orders.filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, detail="Lab Order not found")
    return order


@router.delete(
    "/laborders/{order_id}/",
    status_code=204,
    dependencies=[Security(auth.permission(Permissions.WRITE_RECORDS))],
)
def laborder_delete(
    order_id: str,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    ukrdc3: Session = Depends(get_ukrdc3),
) -> None:
    """Mark a particular lab order for deletion"""
    order = patient_record.lab_orders.filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, detail="Lab Order not found")

    deletes = [
        PVDelete(
            pid=item.pid,
            observation_time=item.observation_time,
            service_id=item.service_id,
        )
        for item in order.result_items
    ]
    ukrdc3.bulk_save_objects(deletes)

    ukrdc3.delete(order)
    ukrdc3.commit()


@router.get(
    "/results/",
    response_model=Page[ResultItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_resultitems(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    service_id: Optional[list[str]] = QueryParam([]),
    order_id: Optional[list[str]] = QueryParam([]),
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    sorter: Sorter = Depends(
        make_sorter(
            [ResultItem.observation_time, ResultItem.entered_on],
            default_sort_by=ResultItem.observation_time,
        )
    ),
):
    """Retreive a specific patient's lab orders"""

    query = patient_record.result_items

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
    "/results/{resultitem_id}/",
    response_model=ResultItemSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def resultitem_get(
    resultitem_id: str, patient_record: PatientRecord = Depends(_get_patientrecord)
) -> ResultItem:
    """Retreive a particular lab result"""
    item = patient_record.result_items.filter(ResultItem.id == resultitem_id).first()
    if not item:
        raise HTTPException(404, detail="Result item not found")
    return item


@router.delete(
    "/results/{resultitem_id}/",
    status_code=204,
    dependencies=[Security(auth.permission(Permissions.WRITE_RECORDS))],
)
def resultitem_delete(
    resultitem_id: str,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    ukrdc3: Session = Depends(get_ukrdc3),
) -> None:
    """Mark a particular lab result for deletion"""
    item = patient_record.result_items.filter(ResultItem.id == resultitem_id).first()
    if not item:
        raise HTTPException(404, detail="Result item not found")

    order: Optional[LabOrder] = item.order

    ukrdc3.delete(item)
    ukrdc3.commit()

    if order and order.result_items.count() == 0:
        ukrdc3.delete(order)
    ukrdc3.commit()


@router.get(
    "/result_services",
    response_model=list[ResultItemServiceSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_result_services(
    patient_record: PatientRecord = Depends(_get_patientrecord),
):
    """Retreive a list of resultitem services available for a specific patient"""
    services = patient_record.result_items.distinct(ResultItem.service_id)
    return [
        ResultItemServiceSchema(
            id=item.service_id,
            description=item.service_id_description,
            standard=item.service_id_std,
        )
        for item in services.all()
    ]
