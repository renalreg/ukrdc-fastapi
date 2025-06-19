from time import time
from typing import Sequence

from sqlalchemy import and_, desc, select

from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.ukrdc import Code

from ukrdc_fastapi.dependencies.database import ErrorsSession, Ukrdc3Session

ukrdc3 = Ukrdc3Session()
session = ErrorsSession()

stmt = select(Code).where(Code.coding_standard == "RR1+")
codes:Sequence[Code] = ukrdc3.scalars(stmt).all()

t0 = time()

for code in codes:
    facility = code.code
    print(f"Scanning facility {facility}...")

    message_stmt = (
        select(Message.ni, Message.received, Message.msg_status)
        .where(and_(Message.facility == facility, Message.ni.isnot(None)))
        .order_by(Message.ni, desc(Message.received))
        .distinct(Message.ni)
    )

    messages = session.scalars(message_stmt).all()

    err:Sequence[Message] = [m for m in messages if m.msg_status == "ERROR"]

    print(f"{len(err)} patients failing:")
    print([m.ni for m in err])

t1 = time()

print(f"Runtime of the program is {t1 - t0}")
