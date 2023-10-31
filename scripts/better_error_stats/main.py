from time import time

from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.ukrdc import Code

from ukrdc_fastapi.dependencies.database import ErrorsSession, Ukrdc3Session

ukrdc3 = Ukrdc3Session()
session = ErrorsSession()

codes = ukrdc3.query(Code).filter(Code.coding_standard == "RR1+").all()

t0 = time()

for code in codes:
    facility = code.code
    print(f"Scanning facility {facility}...")

    q = (
        session.query(Message.ni, Message.received, Message.msg_status)
        .filter(Message.facility == facility)
        .filter(Message.ni != None)  # noqa: E711
        .order_by(Message.ni, Message.received.desc())
        .distinct(Message.ni)
    )

    all = q.all()

    err = [m for m in all if m.msg_status == "ERROR"]

    print(f"{len(err)} patients failing:")
    print([m.ni for m in err])

t1 = time()

print(f"Runtime of the program is {t1 - t0}")
