from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.models.audit import AccessEvent, AuditEvent
from ukrdc_fastapi.utils.sort import make_sqla_sorter

ERROR_SORTER = make_sqla_sorter(
    [Message.id, Message.received, Message.ni], default_sort_by=Message.received
)

AUDIT_SORTER = make_sqla_sorter(
    [AuditEvent.id, AccessEvent.time],
    default_sort_by=AuditEvent.id,
)
