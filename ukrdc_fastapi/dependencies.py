from .database import JtraceSession, Ukrdc3Session


def get_ukrdc3():
    db = Ukrdc3Session()
    try:
        yield db
    finally:
        db.close()


def get_jtrace():
    db = JtraceSession()
    try:
        yield db
    finally:
        db.close()
