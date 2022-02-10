from datetime import datetime
from enum import Enum
from typing import AsyncGenerator, Optional, Union

from fastapi import Depends, Request, Security
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import WorkItem

from ukrdc_fastapi.dependencies import get_auditdb
from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.models.audit import AccessEvent, AuditEvent
from ukrdc_fastapi.schemas.empi import WorkItemExtendedSchema, WorkItemSchema

from .auth import auth


class Resource(Enum):
    PATIENT_RECORD = "PATIENT_RECORD"
    MEDICATIONS = "MEDICATIONS"
    TREATMENTS = "TREATMENTS"
    SURVEYS = "SURVEYS"
    DOCUMENTS = "DOCUMENTS"
    DOCUMENT = "DOCUMENT"
    OBSERVATIONS = "OBSERVATIONS"
    LABORDERS = "LABORDERS"
    LABORDER = "LABORDER"
    RESULTITEMS = "RESULTITEMS"
    RESULTITEM = "RESULTITEM"

    MASTER_RECORD = "MASTER_RECORD"
    MESSAGES = "MESSAGES"
    STATISTICS = "STATISTICS"

    MEMBERSHIP = "MEMBERSHIP"

    PERSON = "PERSON"
    MESSAGE = "MESSAGE"
    WORKITEM = "WORKITEM"

    FACILITY = "FACILITY"


class MasterRecordResource(Enum):
    MESSAGE = "MESSAGE"
    MESSAGES = "MESSAGES"
    STATISTICS = "STATISTICS"


class AuditOperation(Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    READ = "READ"


class RecordOperation(Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    READ = "READ"

    EXPORT_PV = "EXPORT_PV"
    EXPORT_PV_TESTS = "EXPORT_PV_TESTS"
    EXPORT_PV_DOCS = "EXPORT_PV_DOCS"
    EXPORT_RADAR = "EXPORT_RADAR"
    EXPORT_PKB = "EXPORT_PKB"


class MessageOperation(Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    READ = "READ"

    READ_SOURCE = "READ_SOURCE"


class Auditer:
    """
    NOTES:
    In functions returning lists/pages, we'll just need to store the list to a variable
    then add audit rows for each item before returning the list/page, within the view
    function.
    We may end up with verbose code with some duplication, but it should at least be
    clear what's happening, so future devs can easily tweak it.
    The temptation is to make this some "magic" functionality that reads the response
    model and automatically pulls out each audit item, ID etc, but that's not really
    possible, as we don't know what the response model is.
    I will need to think about this more, but for now, I'll just store the list of
    items to audit, and commit the audit rows in the view function.
    """

    def __init__(self, request: Request, auditdb: Session, user: UKRDCUser):
        self.request = request
        self.session = auditdb

        self.event = AccessEvent(
            time=datetime.now(),
            uid=user.id,
            cid=user.cid,
            sub=user.email,
            client_host=request.client.host,
            path=str(request.url),
            method=request.method,
            body=None,
        )

    async def add_request(self):
        """Add the audit request"""
        self.event.body = (await self.request.body()).decode("utf-8") or None

        self.session.add(self.event)
        self.session.flush()

    def add_event(
        self,
        resource: Resource,
        resource_id: Optional[Union[str, int]],
        operation: Optional[Union[RecordOperation, MessageOperation, AuditOperation]],
        parent: Optional[AuditEvent] = None,
    ) -> AuditEvent:
        """Add an audit event

        Args:
            resource (Resource): Resource type
            resource_id (Optional[Union[str, int]]): Resource ID (e.g. PID, Master Record ID etc)
            operation (Optional[Union[RecordOperation, MessageOperation, AuditOperation]]): Audit operation (e.g. READ, UPDATE etc)
            parent (Optional[AuditEvent], optional): Parent AuditEvent. Defaults to None.

        Returns:
            AuditEvent: AuditEvent object
        """
        event = AuditEvent(
            parent_id=parent.id if parent else None,
            access_event_id=self.event.id,
            resource=resource.value if resource else None,
            resource_id=str(resource_id) if resource_id else None,
            operation=operation.value if operation else None,
        )
        self.session.add(event)
        # Flush so that the auto-incrementing ID is available
        self.session.flush()
        # Return the Event so it can be used as a parent event later
        return event

    def add_workitem(
        self,
        workitem: Union[WorkItem, WorkItemSchema, WorkItemExtendedSchema],
        parent: Optional[AuditEvent] = None,
    ) -> AuditEvent:
        """Add a WorkItem and all of its child Person and Master Records to the audit database

        Args:
            workitem (Union[WorkItem, WorkItemSchema, WorkItemExtendedSchema]): WorkItem object
            parent (Optional[AuditEvent], optional): Parent AuditEvent. Defaults to None.

        Returns:
            AuditEvent: AuditEvent object
        """
        workitem_audit = self.add_event(
            Resource.WORKITEM, workitem.id, AuditOperation.READ, parent=parent
        )
        audited_master_ids: set[int] = set()
        audited_person_ids: set[int] = set()
        if workitem.master_record:
            audited_master_ids.add(workitem.master_record.id)
        if workitem.person:
            audited_person_ids.add(workitem.person.id)

        if isinstance(workitem, WorkItemExtendedSchema):
            for master_record in workitem.incoming.master_records:
                audited_master_ids.add(master_record.id)
            for person in workitem.destination.persons:
                audited_person_ids.add(person.id)
            if workitem.destination.master_record:
                audited_master_ids.add(workitem.destination.master_record.id)
            if workitem.incoming.person:
                audited_person_ids.add(workitem.incoming.person.id)

        for person_id in audited_person_ids:
            self.add_event(
                Resource.PERSON,
                person_id,
                AuditOperation.READ,
                parent=workitem_audit,
            )
        for master_id in audited_master_ids:
            self.add_event(
                Resource.MASTER_RECORD,
                master_id,
                AuditOperation.READ,
                parent=workitem_audit,
            )

        return workitem_audit


async def get_auditer(
    request: Request,
    auditdb: Session = Depends(get_auditdb),
    user: UKRDCUser = Security(auth.get_user()),
) -> AsyncGenerator[Auditer, None]:
    """Yeild a new Auditer object with an access event pre-populated

    Yields:
        [Auditer]: Auditer
    """
    auditer = Auditer(request, auditdb, user)
    await auditer.add_request()

    try:
        yield auditer
        auditer.session.commit()
    finally:
        auditer.session.close()
