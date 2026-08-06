from xml.etree.ElementTree import fromstring

import pytest
from ukrdc_sqla.ukrdc import Facility, PatientRecord, ProgramMembership

from tests.utils import days_ago
from ukrdc_fastapi.exceptions import (
    NoActiveMembershipError,
    PKBOutboundDisabledError,
    ResourceNotFoundError,
)
from ukrdc_fastapi.utils.mirth.messages.pkb import (
    EXCLUDED_EXTRACTS,
    build_pkb_membership_message,
    build_pkb_sync_messages,
)


def _create_membership(pid: str, ukrdc3_session):
    membership = ProgramMembership(
        id="MEMBERSHIP_PKB",
        pid=pid,
        programname="PKB",
        fromtime=days_ago(365),
        totime=None,
    )
    ukrdc3_session.add(membership)
    ukrdc3_session.commit()


def _get_message_types(messages: list[str]) -> list[str]:
    message_types: list[str] = []

    for message in messages:
        msg_type = fromstring(message).findtext("msg_type")
        assert msg_type is not None
        message_types.append(msg_type)

    return message_types


def test_build_pkb_membership_message():
    assert (
        build_pkb_membership_message("ukrdcid")
        == "<result><ukrdcid>ukrdcid</ukrdcid></result>"
    )


def test_build_pkb_sync_message(ukrdc3_session):
    pid_1 = "PYTEST01:PV:00000000A"
    _create_membership(pid_1, ukrdc3_session)
    record = ukrdc3_session.get(PatientRecord, pid_1)

    messages = build_pkb_sync_messages(record, ukrdc3_session)
    assert messages == [
        "<result><msg_type>ADT_A28</msg_type><pid>PYTEST01:PV:00000000A</pid></result>",
        "<result><msg_type>MDM_T02_CP</msg_type><pid>PYTEST01:PV:00000000A</pid></result>",
        "<result><msg_type>MDM_T02_DOC</msg_type><pid>PYTEST01:PV:00000000A</pid><id>DOCUMENT_PDF</id></result>",
        "<result><msg_type>MDM_T02_DOC</msg_type><pid>PYTEST01:PV:00000000A</pid><id>DOCUMENT_TXT</id></result>",
        "<result><msg_type>ORU_R01_LAB</msg_type><pid>PYTEST01:PV:00000000A</pid><id>LABORDER1</id></result>",
        "<result><msg_type>ORU_R01_LAB</msg_type><pid>PYTEST01:PV:00000000A</pid><id>LABORDER2</id></result>",
        "<result><msg_type>ORU_R01_OBS</msg_type><pid>PYTEST01:PV:00000000A</pid><id>OBSERVATION1</id></result>",
        "<result><msg_type>ORU_R01_OBS</msg_type><pid>PYTEST01:PV:00000000A</pid><id>OBSERVATION_DIA_1</id></result>",
        "<result><msg_type>ORU_R01_OBS</msg_type><pid>PYTEST01:PV:00000000A</pid><id>OBSERVATION_SYS_1</id></result>",
    ]


def test_build_pkb_sync_message_no_membership(ukrdc3_session):
    pid_1 = "PYTEST01:PV:00000000A"
    record = ukrdc3_session.get(PatientRecord, pid_1)

    with pytest.raises(NoActiveMembershipError):
        build_pkb_sync_messages(record, ukrdc3_session)


def test_build_pkb_sync_message_missing_facility(ukrdc3_session):
    pid_1 = "PYTEST01:PV:00000000A"
    _create_membership(pid_1, ukrdc3_session)
    record = ukrdc3_session.get(PatientRecord, pid_1)

    record.sendingfacility = "MISSING"
    ukrdc3_session.commit()

    with pytest.raises(ResourceNotFoundError):
        build_pkb_sync_messages(record, ukrdc3_session)


def test_build_pkb_sync_disabled_facility(ukrdc3_session):
    pid_1 = "PYTEST01:PV:00000000A"
    _create_membership(pid_1, ukrdc3_session)
    record = ukrdc3_session.get(PatientRecord, pid_1)

    facility = ukrdc3_session.get(Facility, (record.sendingfacility, "RR1+"))
    facility.pkb_out = False
    ukrdc3_session.commit()

    with pytest.raises(PKBOutboundDisabledError):
        build_pkb_sync_messages(record, ukrdc3_session)


@pytest.mark.parametrize("extract", EXCLUDED_EXTRACTS)
def test_build_pkb_sync_disabled_extract(ukrdc3_session, extract):
    pid_1 = "PYTEST01:PV:00000000A"
    _create_membership(pid_1, ukrdc3_session)
    record = ukrdc3_session.get(PatientRecord, pid_1)

    record.sendingextract = extract
    ukrdc3_session.commit()

    with pytest.raises(PKBOutboundDisabledError):
        build_pkb_sync_messages(record, ukrdc3_session)


def test_build_pkb_sync_message_legacy_facility_exclusions(ukrdc3_session):
    pid_1 = "PYTEST01:PV:00000000A"
    _create_membership(pid_1, ukrdc3_session)

    record = ukrdc3_session.get(PatientRecord, pid_1)
    assert record is not None

    facility = ukrdc3_session.get(Facility, (record.sendingfacility, "RR1+"))
    assert facility is not None

    record.sendingextract = "PV"
    facility.pvoutpkb = True
    facility.pkb_msg_exclusions = ["MDM_T02_DOC"]
    facility.pkb_pv_msg_exclusions = None

    ukrdc3_session.commit()

    messages = build_pkb_sync_messages(record, ukrdc3_session)

    assert _get_message_types(messages) == [
        "ADT_A28",
        "MDM_T02_CP",
        "ORU_R01_LAB",
        "ORU_R01_LAB",
        "ORU_R01_OBS",
        "ORU_R01_OBS",
        "ORU_R01_OBS",
    ]


def test_build_pkb_sync_message_pv_exclusions(ukrdc3_session):
    pid_1 = "PYTEST01:PV:00000000A"
    _create_membership(pid_1, ukrdc3_session)

    record = ukrdc3_session.get(PatientRecord, pid_1)
    assert record is not None

    facility = ukrdc3_session.get(Facility, (record.sendingfacility, "RR1+"))
    assert facility is not None

    record.sendingextract = "PV"
    facility.pvoutpkb = True

    # These should be ignored because PV has its own exclusions
    facility.pkb_msg_exclusions = ["ORU_R01_LAB"]
    facility.pkb_ukrdc_msg_exclusions = [
        "ADT_A28",
        "MDM_T02_CP",
        "ORU_R01_LAB",
        "ORU_R01_OBS",
    ]

    facility.pkb_pv_msg_exclusions = ["MDM_T02_DOC"]

    ukrdc3_session.commit()

    messages = build_pkb_sync_messages(record, ukrdc3_session)

    assert _get_message_types(messages) == [
        "ADT_A28",
        "MDM_T02_CP",
        "ORU_R01_LAB",
        "ORU_R01_LAB",
        "ORU_R01_OBS",
        "ORU_R01_OBS",
        "ORU_R01_OBS",
    ]


def test_build_pkb_sync_message_ukrdc_exclusions(ukrdc3_session):
    pid_1 = "PYTEST01:PV:00000000A"
    _create_membership(pid_1, ukrdc3_session)

    record = ukrdc3_session.get(PatientRecord, pid_1)
    assert record is not None

    facility = ukrdc3_session.get(Facility, (record.sendingfacility, "RR1+"))
    assert facility is not None

    record.sendingextract = "UKRDC"
    facility.ukrdcoutpkb = True

    # These should be ignored because UKRDC has its own exclusions
    facility.pkb_msg_exclusions = ["MDM_T02_DOC"]
    facility.pkb_pv_msg_exclusions = ["MDM_T02_DOC"]

    facility.pkb_ukrdc_msg_exclusions = [
        "ADT_A28",
        "MDM_T02_CP",
        "ORU_R01_LAB",
        "ORU_R01_OBS",
    ]

    ukrdc3_session.commit()

    messages = build_pkb_sync_messages(record, ukrdc3_session)

    assert _get_message_types(messages) == [
        "MDM_T02_DOC",
        "MDM_T02_DOC",
    ]


def test_build_pkb_sync_message_empty_pv_exclusions_override_legacy(
    ukrdc3_session,
):
    pid_1 = "PYTEST01:PV:00000000A"
    _create_membership(pid_1, ukrdc3_session)

    record = ukrdc3_session.get(PatientRecord, pid_1)
    assert record is not None

    facility = ukrdc3_session.get(Facility, (record.sendingfacility, "RR1+"))
    assert facility is not None

    record.sendingextract = "PV"
    facility.pvoutpkb = True

    facility.pkb_msg_exclusions = ["MDM_T02_DOC"]
    facility.pkb_pv_msg_exclusions = []

    ukrdc3_session.commit()

    messages = build_pkb_sync_messages(record, ukrdc3_session)

    assert _get_message_types(messages) == [
        "ADT_A28",
        "MDM_T02_CP",
        "MDM_T02_DOC",
        "MDM_T02_DOC",
        "ORU_R01_LAB",
        "ORU_R01_LAB",
        "ORU_R01_OBS",
        "ORU_R01_OBS",
        "ORU_R01_OBS",
    ]


def test_build_pkb_sync_message_null_exclusions_include_all_messages(
    ukrdc3_session,
):
    pid_1 = "PYTEST01:PV:00000000A"
    _create_membership(pid_1, ukrdc3_session)

    record = ukrdc3_session.get(PatientRecord, pid_1)
    assert record is not None

    facility = ukrdc3_session.get(Facility, (record.sendingfacility, "RR1+"))
    assert facility is not None

    record.sendingextract = "PV"
    facility.pvoutpkb = True
    facility.pkb_msg_exclusions = None
    facility.pkb_pv_msg_exclusions = None

    ukrdc3_session.commit()

    messages = build_pkb_sync_messages(record, ukrdc3_session)

    assert _get_message_types(messages) == [
        "ADT_A28",
        "MDM_T02_CP",
        "MDM_T02_DOC",
        "MDM_T02_DOC",
        "ORU_R01_LAB",
        "ORU_R01_LAB",
        "ORU_R01_OBS",
        "ORU_R01_OBS",
        "ORU_R01_OBS",
    ]
