import logging
from typing import List, Optional, Set, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_jtrace, get_ukrdc3
from ukrdc_fastapi.models.empi import LinkRecord, MasterRecord, WorkItem
from ukrdc_fastapi.models.ukrdc import LabOrder, PatientNumber, PatientRecord, PVDelete
from ukrdc_fastapi.schemas.empi import WorkItemSchema
from ukrdc_fastapi.schemas.laborder import LabOrderSchema
from ukrdc_fastapi.schemas.patientrecord import PatientRecordShortSchema

from . import record

router = APIRouter()
router.include_router(record.router, prefix="/record")


@router.get("/records", response_model=List[PatientRecordShortSchema])
def patient_records(ni: str, ukrdc3: Session = Depends(get_ukrdc3)):
    # Only look for data if an NI was given
    if ni:
        pids = ukrdc3.query(PatientNumber.pid).filter(
            PatientNumber.patientid == ni,
            PatientNumber.numbertype == "NI",
        )
        if pids.count() == 0:
            return []

        # Find different ukrdcids
        query = (
            ukrdc3.query(PatientRecord.ukrdcid)
            .filter(PatientRecord.pid.in_(pids))
            .distinct()
        )

        ukrdcids = [ukrdcid for (ukrdcid,) in query.all()]

        if not ukrdcids:
            return []

        # Find all the records with ukrdc ids
        records = (
            ukrdc3.query(PatientRecord)
            .filter(PatientRecord.ukrdcid.in_(ukrdcids))
            .all()
        )
        return records
    return []


@router.get("/laborders/{order_id}", response_model=LabOrderSchema)
def laborder_get(self, order_id: str, ukrdc3: Session = Depends(get_ukrdc3)):
    laborder = ukrdc3.query(LabOrder).get(order_id)
    if not laborder:
        raise HTTPException(404, detail="Lab order not found")
    return laborder


@router.delete("/laborders/{order_id}", status_code=204)
def laborder_delete(self, order_id: str, ukrdc3: Session = Depends(get_ukrdc3)):
    laborder: LabOrder = ukrdc3.query(LabOrder).get(order_id)
    pid = laborder.pid
    deletes = [
        PVDelete(
            pid=pid,
            observation_time=item.observation_time,
            service_id=item.service_id,
        )
        for item in laborder.result_items
    ]
    ukrdc3.bulk_save_objects(deletes)

    for item in deletes:
        logging.info(
            "DELETING result item: %s - %s (%s)",
            item.pid,
            item.service_id,
            item.observation_time,
        )
    logging.info("DELETING lab order: %s - %s", laborder.id, laborder.pid)

    ukrdc3.delete(laborder)
    ukrdc3.commit()


@router.get("/workitems", response_model=List[WorkItemSchema])
def workitems(
    self,
    ukrdcid: Optional[List[str]] = Query(None),
    jtrace: Session = Depends(get_jtrace),
):
    records: List[Tuple[int]] = (
        jtrace.query(MasterRecord.id)
        .filter(
            MasterRecord.nationalid_type == "UKRDC",
            MasterRecord.nationalid.in_(ukrdcid),
        )
        .all()
    )
    flat_ids: List[int] = [masterid for masterid, in records]

    seen_master_ids: Set[int] = set(flat_ids)
    seen_person_ids: Set[int] = set()
    found_new: bool = True
    while found_new:
        links: List[LinkRecord] = (
            jtrace.query(LinkRecord)
            .filter(
                (LinkRecord.master_id.in_(seen_master_ids))
                | (LinkRecord.person_id.in_(seen_person_ids))
            )
            .all()
        )

        master_ids: Set[int] = {item.master_id for item in links}
        person_ids: Set[int] = {item.person_id for item in links}
        if seen_master_ids.issuperset(master_ids) and seen_person_ids.issuperset(
            person_ids
        ):
            found_new = False
        seen_master_ids |= master_ids
        seen_person_ids |= person_ids

    workitems = jtrace.query(WorkItem).filter(
        (WorkItem.master_id.in_(seen_master_ids))
        | (WorkItem.person_id.in_(seen_person_ids))
    )
    return workitems.filter(WorkItem.status == 1).all()
