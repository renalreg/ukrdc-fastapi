from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import Depends, Request, Security
from sqlalchemy.orm.session import Session

from ukrdc_fastapi.dependencies import get_auditsdb
from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.models.audit import (
    AccessEvent,
    MasterRecordEvent,
    MessageEvent,
    PatientRecordEvent,
    PersonEvent,
)

from .auth import auth


class RecordResource(Enum):
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

    def __init__(
        self,
        request: Request,
        auditdb: Session = Depends(get_auditsdb),
        user: UKRDCUser = Security(auth.get_user()),
    ):
        self.session = auditdb

        self.event = AccessEvent(
            time=datetime.now(),
            uid=user.id,
            cid=user.cid,
            sub=user.email,
            client_host=request.client.host,
            path=str(request.url),
            method=request.method,
            query_params=dict(request.query_params),
            path_params=dict(request.path_params),
        )

        auditdb.add(self.event)
        auditdb.commit()

    def add_patient_record(
        self,
        pid: str,
        resource: Optional[RecordResource],
        resource_id: Optional[str],
        operation: Optional[AuditOperation],
    ):
        self.session.add(
            PatientRecordEvent(
                event=self.event.event,
                pid=pid,
                resource=resource.value if resource else None,
                resource_id=resource_id,
                operation=operation.value if operation else None,
            )
        )
        self.session.commit()

    def add_master_record(
        self,
        id_: int,
        operation: Optional[AuditOperation],
    ):
        self.session.add(
            MasterRecordEvent(
                event=self.event.event,
                master_id=id_,
                operation=operation.value if operation else None,
            )
        )
        self.session.commit()

    def add_person(
        self,
        id_: int,
        operation: Optional[AuditOperation],
    ):
        self.session.add(
            PersonEvent(
                event=self.event.event,
                person_id=id_,
                operation=operation.value if operation else None,
            )
        )
        self.session.commit()

    def add_message(
        self,
        id_: int,
        operation: Optional[MessageOperation],
    ):
        self.session.add(
            MessageEvent(
                event=self.event.event,
                message_id=id_,
                operation=operation.value if operation else None,
            )
        )
        self.session.commit()
