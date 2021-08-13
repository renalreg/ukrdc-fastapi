import hashlib
from dataclasses import dataclass

from fastapi.exceptions import HTTPException
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person, PidXRef, WorkItem
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.query.patientrecords import get_patientrecord
from ukrdc_fastapi.schemas.delete import (
    DeletePIDFromEMPISchema,
    DeletePIDPreviewSchema,
    DeletePIDResponseSchema,
)
from ukrdc_fastapi.schemas.patientrecord import PatientRecordFullSchema


class ConfirmationError(HTTPException):
    def __init__(self) -> None:
        super().__init__(400, detail="Incorrect hash provided to delete function.")


class OpenWorkItemError(HTTPException):
    def __init__(self, work_item_ids: list[str]) -> None:
        _id_strings = ", ".join([f"Work Item ID {id_}" for id_ in work_item_ids])
        super().__init__(
            400,
            detail=f"Cannot delete a patient with open Work Items ({_id_strings}).",
        )


@dataclass
class EMPIDeleteItems:
    persons: list[Person]
    master_records: list[MasterRecord]
    pidxrefs: list[PidXRef]
    work_items: list[WorkItem]
    link_records: list[LinkRecord]


def _find_empi_items_to_delete(jtrace: Session, pid: str) -> EMPIDeleteItems:
    to_delete = EMPIDeleteItems(
        persons=[], master_records=[], pidxrefs=[], work_items=[], link_records=[]
    )
    to_delete.pidxrefs = jtrace.query(PidXRef).filter(PidXRef.pid == pid).all()
    to_delete.persons = jtrace.query(Person).filter(Person.localid == pid).all()

    for person_record in to_delete.persons:
        # Find work items related to person
        to_delete.work_items.extend(
            jtrace.query(WorkItem).filter(WorkItem.person_id == person_record.id).all()
        )

        # Find link records related to person
        link_records_related_to_person = (
            jtrace.query(LinkRecord)
            .filter(LinkRecord.person_id == person_record.id)
            .all()
        )
        to_delete.link_records.extend(link_records_related_to_person)

        # Find master IDs directly related to Person
        master_ids = [
            link_record.master_id for link_record in link_records_related_to_person
        ]

        for master_id in master_ids:
            # Find link records related to the Master Record but NOT the Person
            # currently being deleted
            link_records_related_to_other_persons = (
                jtrace.query(LinkRecord)
                .filter(
                    LinkRecord.master_id == master_id,
                    LinkRecord.person_id != person_record.id,
                )
                .all()
            )

            # If the above query comes back empty, the Master Record is ONLY
            # linked to the Person being deleted, and so can itself be deleted
            if len(link_records_related_to_other_persons) == 0:
                master_record = jtrace.query(MasterRecord).get(master_id)
                to_delete.master_records.append(master_record)
                if master_record:
                    # Find work items related to master record
                    to_delete.work_items.extend(
                        jtrace.query(WorkItem)
                        .filter(WorkItem.master_id == master_record.id)
                        .all()
                    )

    open_work_items: list[WorkItem] = [
        work_item for work_item in to_delete.work_items if work_item.status == 1
    ]
    if len(open_work_items) > 0:
        raise OpenWorkItemError([str(work_item.id) for work_item in open_work_items])

    return to_delete


def _create_delete_pid_summary(
    record_to_delete: PatientRecord,
    empi_to_delete: EMPIDeleteItems,
    committed: bool = False,
) -> DeletePIDResponseSchema:

    empi_to_delete_summary = DeletePIDFromEMPISchema.from_orm(empi_to_delete)
    record_to_delete_summary = PatientRecordFullSchema.from_orm(record_to_delete)

    to_delete_summary = DeletePIDPreviewSchema(
        patient_record=record_to_delete_summary, empi=empi_to_delete_summary
    )

    to_delete_json = to_delete_summary.json()
    # We ignore Bandit warnings here as MD5 is not being used for security purposes
    to_delete_hash = hashlib.md5(to_delete_json.encode()).hexdigest()  # nosec

    return DeletePIDResponseSchema(
        patient_record=record_to_delete_summary,
        empi=empi_to_delete_summary,
        hash=to_delete_hash,
        committed=committed,
    )


def summarise_delete_pid(
    ukrdc3: Session, jtrace: Session, pid: str, user: UKRDCUser
) -> DeletePIDResponseSchema:
    """Create a summary of the records to be deleted.

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        jtrace (Session): JTRACE SQLAlchemy session
        pid (str): PatientRecord PID
        user (UKRDCUser): User object

    Returns:
        DeletePIDResponseSchema: Summary of database items to be deleted
    """
    record_to_delete = get_patientrecord(ukrdc3, pid, user)
    empi_to_delete = _find_empi_items_to_delete(jtrace, record_to_delete.pid)

    return _create_delete_pid_summary(record_to_delete, empi_to_delete)


def delete_pid(
    ukrdc3: Session, jtrace: Session, pid: str, hash_: str, user: UKRDCUser
) -> DeletePIDResponseSchema:
    """Delete a patient record and related records from the database.

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        jtrace (Session): JTRACE SQLAlchemy session
        pid (str): PatientRecord PID
        hash_ (str): MD5 hash of the JSON summary of the records to be deleted
        user (UKRDCUser): User object

    Raises:
        ConfirmationError: Mismatched MD5 hash provided

    Returns:
        DeletePIDResponseSchema:  Summary of database items deleted
    """
    record_to_delete = get_patientrecord(ukrdc3, pid, user)
    empi_to_delete = _find_empi_items_to_delete(jtrace, record_to_delete.pid)

    summary = _create_delete_pid_summary(
        record_to_delete, empi_to_delete, committed=True
    )

    if hash_ != summary.hash:
        raise ConfirmationError()

    ukrdc3.delete(record_to_delete)

    for person in empi_to_delete.persons:
        jtrace.delete(person)

    for master_record in empi_to_delete.master_records:
        jtrace.delete(master_record)

    for pidxrefs in empi_to_delete.pidxrefs:
        jtrace.delete(pidxrefs)

    for work_item in empi_to_delete.work_items:
        jtrace.delete(work_item)

    for link_record in empi_to_delete.link_records:
        jtrace.delete(link_record)

    ukrdc3.commit()
    jtrace.commit()

    return summary
