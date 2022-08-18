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
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    RecordOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.delete import delete_pid, summarise_delete_pid
from ukrdc_fastapi.query.patientrecords import (
    get_patientrecords_related_to_patientrecord,
)
from ukrdc_fastapi.schemas.delete import DeletePidRequest, DeletePIDResponseSchema
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
    PatientRecordSummarySchema,
)
from ukrdc_fastapi.schemas.survey import SurveySchema
from ukrdc_fastapi.schemas.treatment import TreatmentSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import SQLASorter, make_sqla_sorter

from . import export, update
from .dependencies import _get_patientrecord

router = APIRouter()
router.include_router(export.router, prefix="/{pid}/export")
router.include_router(update.router, prefix="/{pid}/update")


# Self-resources


@router.get(
    "/{pid}",
    response_model=PatientRecordSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient record"""
    # For some reason the fastAPI response_model doesn't call our master_record_compute
    # validator, meaning we don't get a populated master record unless we explicitly
    # call it here.
    record: PatientRecordSchema = PatientRecordSchema.from_orm_with_master_record(
        patient_record, jtrace
    )
    audit.add_event(Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ)
    return record


@router.post(
    "/{pid}/delete",
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
    audit: Auditer = Depends(get_auditer),
    args: Optional[DeletePidRequest] = None,
):
    """Delete a specific patient record and all its associated data"""
    summary: DeletePIDResponseSchema
    audit_op: AuditOperation

    if args and args.hash:
        summary = delete_pid(ukrdc3, jtrace, pid, args.hash, user)
        audit_op = AuditOperation.DELETE
    else:
        summary = summarise_delete_pid(ukrdc3, jtrace, pid, user)
        audit_op = AuditOperation.READ

    record_audit = audit.add_event(Resource.PATIENT_RECORD, pid, audit_op)
    if summary.empi:
        for person in summary.empi.persons:
            audit.add_event(Resource.PERSON, person.id, audit_op, parent=record_audit)
        for master_record in summary.empi.master_records:
            audit.add_event(
                Resource.MASTER_RECORD, master_record.id, audit_op, parent=record_audit
            )

    return summary


@router.get(
    "/{pid}/related",
    response_model=list[PatientRecordSummarySchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_related(
    pid: str,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive patient records related to a specific patient record"""
    related = get_patientrecords_related_to_patientrecord(
        ukrdc3, jtrace, pid, user
    ).all()

    record_audit = audit.add_event(Resource.PATIENT_RECORD, pid, RecordOperation.READ)
    for record in related:
        audit.add_event(
            Resource.PATIENT_RECORD,
            record.pid,
            RecordOperation.READ,
            parent=record_audit,
        )

    return related


# Internal resources


@router.get(
    "/{pid}/medications",
    response_model=list[MedicationSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_medications(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's medications"""
    audit.add_event(
        Resource.MEDICATIONS,
        None,
        RecordOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ
        ),
    )
    return patient_record.medications.all()


@router.get(
    "/{pid}/treatments",
    response_model=list[TreatmentSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_treatments(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's treatments"""
    audit.add_event(
        Resource.TREATMENTS,
        None,
        RecordOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ
        ),
    )
    return patient_record.treatments.all()


@router.get(
    "/{pid}/surveys",
    response_model=list[SurveySchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_surveys(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's surveys"""
    audit.add_event(
        Resource.SURVEYS,
        None,
        RecordOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ
        ),
    )
    return patient_record.surveys.all()


# Complex internal resources


@router.get(
    "/{pid}/observations",
    response_model=Page[ObservationSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_observations(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    code: Optional[list[str]] = QueryParam([]),
    sorter: SQLASorter = Depends(
        make_sqla_sorter(
            [Observation.observation_time, Observation.updated_on],
            default_sort_by=Observation.observation_time,
        )
    ),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's lab orders"""
    observations = patient_record.observations
    if code:
        observations = observations.filter(Observation.observation_code.in_(code))

    audit.add_event(
        Resource.OBSERVATIONS,
        None,
        RecordOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ
        ),
    )

    return paginate(sorter.sort(observations))


@router.get(
    "/{pid}/observation_codes",
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
    "/{pid}/laborders",
    response_model=Page[LabOrderShortSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_laborders(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's lab orders"""
    audit.add_event(
        Resource.LABORDERS,
        None,
        RecordOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ
        ),
    )

    return paginate(
        patient_record.lab_orders.order_by(LabOrder.specimen_collected_time.desc())
    )


@router.get(
    "/{pid}/laborders/{order_id}",
    response_model=LabOrderSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_laborder(
    order_id: str,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
) -> LabOrder:
    """Retreive a particular lab order"""
    order = patient_record.lab_orders.filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, detail="Lab Order not found")

    audit.add_event(
        Resource.LABORDER,
        order_id,
        RecordOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ
        ),
    )

    return order


@router.delete(
    "/{pid}/laborders/{order_id}",
    dependencies=[Security(auth.permission(Permissions.WRITE_RECORDS))],
)
def patient_laborder_delete(
    order_id: str,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    ukrdc3: Session = Depends(get_ukrdc3),
    audit: Auditer = Depends(get_auditer),
) -> Response:
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

    # Audit the laborder delete and then each resulitem delete
    order_audit = audit.add_event(
        Resource.LABORDER,
        order_id,
        RecordOperation.DELETE,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.UPDATE
        ),
    )
    for item in order.result_items:
        audit.add_event(
            Resource.RESULTITEM,
            item.id,
            RecordOperation.DELETE,
            parent=order_audit,
        )

    ukrdc3.bulk_save_objects(deletes)
    ukrdc3.delete(order)
    ukrdc3.commit()

    return Response(status_code=204)


@router.get(
    "/{pid}/results",
    response_model=Page[ResultItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_results(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    service_id: Optional[list[str]] = QueryParam([]),
    order_id: Optional[list[str]] = QueryParam([]),
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    sorter: SQLASorter = Depends(
        make_sqla_sorter(
            [ResultItem.observation_time, ResultItem.entered_on],
            default_sort_by=ResultItem.observation_time,
        )
    ),
    audit: Auditer = Depends(get_auditer),
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

    audit.add_event(
        Resource.RESULTITEMS,
        None,
        RecordOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ
        ),
    )

    return paginate(sorter.sort(query))


@router.get(
    "/{pid}/results/{resultitem_id}",
    response_model=ResultItemSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_result(
    resultitem_id: str,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
) -> ResultItem:
    """Retreive a particular lab result"""
    item = patient_record.result_items.filter(ResultItem.id == resultitem_id).first()
    if not item:
        raise HTTPException(404, detail="Result item not found")

    audit.add_event(
        Resource.RESULTITEM,
        resultitem_id,
        RecordOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ
        ),
    )

    return item


@router.delete(
    "/{pid}/results/{resultitem_id}",
    dependencies=[Security(auth.permission(Permissions.WRITE_RECORDS))],
)
def patient_result_delete(
    resultitem_id: str,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    ukrdc3: Session = Depends(get_ukrdc3),
    audit: Auditer = Depends(get_auditer),
) -> Response:
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

    audit.add_event(
        Resource.RESULTITEM,
        resultitem_id,
        RecordOperation.DELETE,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.UPDATE
        ),
    )

    return Response(status_code=204)


@router.get(
    "/{pid}/result_services",
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


@router.get(
    "/{pid}/documents",
    response_model=Page[DocumentSummarySchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_documents(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    sorter: SQLASorter = Depends(
        make_sqla_sorter(
            [Document.documenttime, Document.updatedon],
            default_sort_by=Document.documenttime,
        )
    ),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's documents"""
    audit.add_event(
        Resource.DOCUMENTS,
        None,
        RecordOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ
        ),
    )
    # NOTE: We defer the 'stream' column to avoid sending the full PDF file content
    # when we're just querying the list of documents.
    return paginate(sorter.sort(patient_record.documents.options(defer("stream"))))


@router.get(
    "/{pid}/documents/{document_id}",
    response_model=DocumentSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_document(
    document_id: str,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's document information"""
    document_obj = patient_record.documents.filter(Document.id == document_id).first()
    if not document_obj:
        raise HTTPException(404, detail="Document not found")

    audit.add_event(
        Resource.DOCUMENT,
        document_id,
        RecordOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ
        ),
    )

    return document_obj


@router.get(
    "/{pid}/documents/{document_id}/download",
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_document_download(
    document_id: str,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's document file"""
    document_obj: Optional[Document] = patient_record.documents.filter(
        Document.id == document_id
    ).first()
    if not document_obj:
        raise HTTPException(404, detail="Document not found")

    audit.add_event(
        Resource.DOCUMENT,
        document_id,
        RecordOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ
        ),
    )

    media_type: str
    stream: bytes
    filename: str
    if not document_obj.filetype:
        media_type = "text/csv"
        stream = (document_obj.notetext or "").encode()
        filename = f"{document_obj.documentname}.txt"
    else:
        media_type = document_obj.filetype
        stream = document_obj.stream or b""
        filename = document_obj.filename or document_obj.documentname or "NoFileName"

    response = Response(content=stream, media_type=media_type)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response
