import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Security
from fastapi import Query as QueryParam
from fastapi.responses import Response
from sqlalchemy.orm import Session
from starlette.status import HTTP_204_NO_CONTENT
from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.ukrdc import (
    Observation,
    PatientRecord,
    ResultItem,
)

from ukrdc_fastapi.dependencies import get_auditdb, get_errorsdb, get_jtrace, get_ukrdc3
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    RecordOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.permissions.messages import (
    apply_message_list_permissions,
    assert_message_permissions,
)
from ukrdc_fastapi.query.audit import get_auditevents_related_to_patientrecord
from ukrdc_fastapi.query.delete import (
    delete_patientrecord,
    summarise_delete_patientrecord,
)
from ukrdc_fastapi.query.messages import get_messages_related_to_patientrecord
from ukrdc_fastapi.schemas.audit import AuditEventSchema
from ukrdc_fastapi.schemas.delete import DeletePidRequest, DeletePIDResponseSchema
from ukrdc_fastapi.schemas.laborder import (
    ResultItemServiceSchema,
)
from ukrdc_fastapi.schemas.medication import MedicationSchema
from ukrdc_fastapi.schemas.message import MessageSchema, MinimalMessageSchema
from ukrdc_fastapi.schemas.observation import ObservationSchema
from ukrdc_fastapi.schemas.patientrecord import (
    PatientRecordSchema,
)
from ukrdc_fastapi.schemas.survey import SurveySchema
from ukrdc_fastapi.schemas.treatment import TreatmentSchema
from ukrdc_fastapi.sorters import AUDIT_SORTER, ERROR_SORTER
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import SQLASorter, make_sqla_sorter

from . import export, update, results, laborders, documents, diagnoses
from .dependencies import _get_patientrecord

router = APIRouter(tags=["Patient Records"])
router.include_router(export.router, prefix="/{pid}/export")
router.include_router(update.router, prefix="/{pid}/update")
router.include_router(results.router, prefix="/{pid}/results")
router.include_router(laborders.router, prefix="/{pid}/laborders")
router.include_router(documents.router, prefix="/{pid}/documents")
router.include_router(diagnoses.router, prefix="/{pid}/diagnoses")


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


@router.get(
    "/{pid}/audit",
    response_model=Page[AuditEventSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS_AUDIT))],
)
def patient_audit(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    ukrdc3: Session = Depends(get_ukrdc3),
    auditdb: Session = Depends(get_auditdb),
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    sorter: SQLASorter = Depends(AUDIT_SORTER),
):
    """
    Retreive a page of audit events related to a particular master record.
    """
    page = paginate(
        sorter.sort(
            get_auditevents_related_to_patientrecord(
                patient_record, auditdb, since=since, until=until
            )
        )
    )

    for item in page.items:  # type: ignore
        item.populate_identifiers(None, ukrdc3)

    return page


@router.get(
    "/{pid}/messages",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_messages(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: Optional[list[str]] = QueryParam(None),
    channel: Optional[list[str]] = QueryParam(None),
    user: UKRDCUser = Security(auth.get_user()),
    errorsdb: Session = Depends(get_errorsdb),
    sorter: SQLASorter = Depends(ERROR_SORTER),
    audit: Auditer = Depends(get_auditer),
):
    """
    Retreive a list of messages related to a particular patient record.
    By default returns message created within the last 365 days.
    """
    messages = get_messages_related_to_patientrecord(
        patient_record,
        errorsdb,
        statuses=status,
        channels=channel,
        since=since,
        until=until,
    )

    # Apply permissions
    messages = apply_message_list_permissions(messages, user)

    # Add audit events
    audit.add_event(
        Resource.MESSAGES,
        None,
        AuditOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.READ
        ),
    )
    return paginate(sorter.sort(messages))


@router.get(
    "/{pid}/latest_message",
    response_model=MinimalMessageSchema,
    responses={204: {"model": None}},
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_record_latest_message(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    user: UKRDCUser = Security(auth.get_user()),
    errorsdb: Session = Depends(get_errorsdb),
):
    """
    Retreive a minimal representation of the latest file received for the patient,
    if received within the last year."""

    # Get messages related to the master record
    msgs = (
        get_messages_related_to_patientrecord(
            patient_record,
            errorsdb,
            since=datetime.datetime.utcnow() - datetime.timedelta(days=365),
        )
        .filter(Message.facility != "TRACING")
        .filter(Message.filename.isnot(None))
    )

    # Apply permissions
    msgs = apply_message_list_permissions(msgs, user)

    # Get latest message
    latest = msgs.order_by(Message.received.desc()).first()

    if not latest:
        return Response(status_code=HTTP_204_NO_CONTENT)

    assert_message_permissions(latest, user)

    return latest


@router.post(
    "/{pid}/delete",
    dependencies=[
        Security(
            auth.permission([Permissions.READ_RECORDS, Permissions.DELETE_RECORDS])
        )
    ],
)
def patient_delete(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    ukrdc3: Session = Depends(get_ukrdc3),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
    args: Optional[DeletePidRequest] = None,
):
    """Delete a specific patient record and all its associated data"""
    summary: DeletePIDResponseSchema
    audit_op: AuditOperation

    if args and args.hash:
        summary = delete_patientrecord(patient_record, ukrdc3, jtrace, args.hash)
        audit_op = AuditOperation.DELETE
    else:
        summary = summarise_delete_patientrecord(patient_record, jtrace)
        audit_op = AuditOperation.READ

    record_audit = audit.add_event(
        Resource.PATIENT_RECORD, patient_record.pid, audit_op
    )
    if summary.empi:
        for person in summary.empi.persons:
            audit.add_event(Resource.PERSON, person.id, audit_op, parent=record_audit)
        for master_record in summary.empi.master_records:
            audit.add_event(
                Resource.MASTER_RECORD, master_record.id, audit_op, parent=record_audit
            )

    return summary


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


# Available codes used to filter other resources


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
