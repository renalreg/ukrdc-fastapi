from fastapi import Depends
from ukrdc_sqla.empi import WorkItem
from ukrdc_sqla.ukrdc import (
    DialysisSession,
    Document,
    Medication,
    Observation,
    ResultItem,
    Survey,
    Transplant,
    Treatment,
)
from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.models.audit import AccessEvent, AuditEvent
from ukrdc_fastapi.utils.sort import make_sqla_sorter, make_object_sorter, OrderBy

WORKITEM_SORTER = Depends(
    make_sqla_sorter(
        [WorkItem.id, WorkItem.last_updated, WorkItem.master_id, WorkItem.person_id],
        default_sort_by=WorkItem.last_updated,
    )
)

DOCUMENT_SORTER = Depends(
    make_sqla_sorter(
        [Document.documenttime, Document.updatedon],
        default_sort_by=Document.documenttime,
    )
)

RESULT_SORTER = Depends(
    make_sqla_sorter(
        [ResultItem.observation_time, ResultItem.entered_on],
        default_sort_by=ResultItem.observation_time,
    )
)

MEDICATION_SORTER = Depends(
    make_sqla_sorter(
        [Medication.fromtime, Medication.totime],
        default_sort_by=Medication.fromtime,
    )
)

TREATMENT_SORTER = Depends(
    make_sqla_sorter(
        [Treatment.fromtime, Treatment.totime],
        default_sort_by=Treatment.fromtime,
    )
)

TRANSPLANT_SORTER = Depends(
    make_sqla_sorter(
        [Transplant.proceduretime, Transplant.creation_date],
        default_sort_by=Transplant.proceduretime,
    )
)

SURVEY_SORTER = Depends(
    make_sqla_sorter(
        [Survey.surveytime, Survey.updatedon],
        default_sort_by=Survey.surveytime,
    )
)

OBSERVATION_SORTER = Depends(
    make_sqla_sorter(
        [Observation.observation_time, Observation.updated_on],
        default_sort_by=Observation.observation_time,
    )
)

DIALYSIS_SESSION_SORTER = Depends(
    make_sqla_sorter(
        [DialysisSession.proceduretime, DialysisSession.creation_date],
        default_sort_by=DialysisSession.proceduretime,
    )
)


ERROR_SORTER = Depends(
    make_sqla_sorter(
        [Message.id, Message.received, Message.ni], default_sort_by=Message.received
    )
)

AUDIT_SORTER = Depends(
    make_sqla_sorter(
        [AuditEvent.id, AccessEvent.time],
        default_sort_by=AuditEvent.id,
    )
)

WORK_ITEM_GROUP_SORTER = Depends(
    make_object_sorter(
        "WorkItemGroupSorterEnum",
        ["work_item_count", "master_record.id", "master_record.last_updated"],
        default_sort_by="work_item_count",
        default_order_by=OrderBy.DESC,
    )
)


FACILITY_ENUM_SORTER = Depends(
    make_object_sorter(
        "FacilitySorterEnum",
        [
            "id",
            "statistics.total_patients",
            "statistics.patients_receiving_message_error",
            "data_flow.pkb_out",
            "last_message_received_at",
        ],
    )
)
