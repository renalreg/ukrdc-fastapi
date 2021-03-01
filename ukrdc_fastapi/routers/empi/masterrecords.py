from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Query, Session

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.models.empi import MasterRecord, Person, WorkItem
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, PersonSchema, WorkItemSchema
from ukrdc_fastapi.utils.filters import _find_related_ids
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


@router.get("/", response_model=Page[MasterRecordSchema])
def master_records(ni: Optional[str] = None, jtrace: Session = Depends(get_jtrace)):
    """Retreive a list of master records from the EMPI"""
    records: Query = jtrace.query(MasterRecord)
    if ni:
        records = records.filter(MasterRecord.nationalid == ni)
    return paginate(records)


@router.get("/{record_id}", response_model=MasterRecordSchema)
def master_record_detail(record_id: str, jtrace: Session = Depends(get_jtrace)):
    """Retreive a particular master record from the EMPI"""
    record: Query = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")

    return record


@router.get("/{record_id}/related", response_model=List[MasterRecordSchema])
def master_record_related(record_id: str, jtrace: Session = Depends(get_jtrace)):
    """Retreive a list of other master records related to a particular master record"""
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")

    related_master_ids, _ = _find_related_ids([record.nationalid], jtrace)

    other_records = jtrace.query(MasterRecord).filter(
        MasterRecord.id.in_(related_master_ids)
    )

    return other_records.all()


@router.get("/{record_id}/workitems", response_model=List[WorkItemSchema])
def master_record_workitems(record_id: str, jtrace: Session = Depends(get_jtrace)):
    """Retreive a list of work items related to a particular master record."""
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")

    related_workitems: Query = jtrace.query(WorkItem).filter(
        WorkItem.master_id == record.id,
        WorkItem.status == 1,
    )

    return related_workitems.all()


@router.get("/{record_id}/persons", response_model=List[PersonSchema])
def master_record_persons(record_id: str, jtrace: Session = Depends(get_jtrace)):
    """Retreive a list of person records related to a particular master record."""
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")

    _, related_person_ids = _find_related_ids([record.nationalid], jtrace)

    persons: Query = jtrace.query(Person).filter(Person.id.in_(related_person_ids))

    return persons.all()
