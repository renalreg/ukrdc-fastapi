from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.responses import Response
from sqlalchemy.orm import defer
from ukrdc_sqla.ukrdc import (
    Document,
    PatientRecord,
)

from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.schemas.patientrecord.documents import (
    DocumentSchema,
    DocumentSummarySchema,
)
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import SQLASorter, make_sqla_sorter

from .dependencies import _get_patientrecord

router = APIRouter()


@router.get(
    "",
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
        AuditOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.READ
        ),
    )
    # NOTE: We defer the 'stream' column to avoid sending the full PDF file content
    # when we're just querying the list of documents.
    return paginate(sorter.sort(patient_record.documents.options(defer("stream"))))


@router.get(
    "/{document_id}",
    response_model=DocumentSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_document(
    document_id: str,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's document information"""
    document_obj = patient_record.documents.where(Document.id == document_id).first()
    if not document_obj:
        raise HTTPException(404, detail="Document not found")

    audit.add_event(
        Resource.DOCUMENT,
        document_id,
        AuditOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.READ
        ),
    )

    return document_obj


@router.get(
    "/{document_id}/download",
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_document_download(
    document_id: str,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's document file"""
    document_obj: Optional[Document] = patient_record.documents.where(
        Document.id == document_id
    ).first()
    if not document_obj:
        raise HTTPException(404, detail="Document not found")

    audit.add_event(
        Resource.DOCUMENT,
        document_id,
        AuditOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.READ
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
