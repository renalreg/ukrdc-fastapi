from tests.utils import days_ago
from ukrdc_sqla.ukrdc import PatientRecord, ProgramMembership
from ukrdc_fastapi.utils.mirth.messages.mrc import build_mrc_sync_message


def _create_membership(pid: str, ukrdc3_session):
    membership = ProgramMembership(
        id="MEMBERSHIP_MRC",
        pid=pid,
        programname="MRC",
        fromtime=days_ago(365),
        totime=None,
    )
    ukrdc3_session.add(membership)
    ukrdc3_session.commit()


def test_build_mrc_sync_message(ukrdc3_session):
    pid_1 = "PYTEST01:PV:00000000A"
    _create_membership(pid_1, ukrdc3_session)
    record = ukrdc3_session.get(PatientRecord, pid_1)

    message = build_mrc_sync_message(record, ukrdc3_session)

    assert message == "<result><pid>PYTEST01:PV:00000000A</pid></result>"
