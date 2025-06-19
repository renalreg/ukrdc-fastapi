import datetime
import json
from typing import List

from sqlalchemy import and_, select
from sqlalchemy.orm import Session
from ukrdc_fastapi.dependencies.audit import AuditOperation, Resource
from ukrdc_fastapi.dependencies.database import AuditSession
from ukrdc_fastapi.models.audit import AuditEvent


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    raise TypeError("Type %s not serializable" % type(obj))


session: Session = AuditSession()

stmt = select(AuditEvent).where(
    and_(
        AuditEvent.resource == Resource.MEMBERSHIP.value,
        AuditEvent.operation == AuditOperation.CREATE.value,
        AuditEvent.resource_id == "PKB",
    )
)

membership_creations = session.scalars(stmt).all()

print(len(membership_creations))

creation_events: dict[str, List[datetime.datetime]] = {}
uid_email_map: dict[str, set[str]] = {}

i = 0

for event in membership_creations:
    even:AuditEvent
    uid:str = event.access_event.uid

    if uid not in creation_events:
        creation_events[uid] = []
    if uid not in uid_email_map:
        uid_email_map[uid] = set()
    if event.access_event.sub:
        uid_email_map[uid].add(event.access_event.sub)
    creation_events[uid].append(event.access_event.time)

    i += 1
    if i % 100 == 0:
        print(i)

print(uid_email_map)
print(creation_events)

with open("./scripts/analytics/output/uids.json", "w") as f1:
    json.dump(
        uid_email_map,
        f1,
        default=json_serial,
    )

with open("./scripts/analytics/output/events.json", "w") as f2:
    json.dump(
        creation_events,
        f2,
        default=json_serial,
    )
