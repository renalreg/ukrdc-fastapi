import datetime

from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.schemas.patient import AddressSchema, NameSchema
from ukrdc_fastapi.utils.mirth.messages.rda import build_demographic_update_message


def test_build_demographic_update_message(ukrdc3_session):
    PID_1 = "PYTEST01:PV:00000000A"
    record = ukrdc3_session.query(PatientRecord).get(PID_1)

    message = build_demographic_update_message(
        record,
        name=NameSchema(given="NEWGIVEN", family="NEWFAMILY"),
        birth_time=datetime.date(1985, 1, 1),
        gender="9",
        address=AddressSchema(postcode="XX0 1TT"),
    )

    assert (
        message
        == """
<?xml version="1.0" encoding="UTF-8"?>
<ns0:PatientRecord xmlns:ns0="http://www.rixg.org.uk/"><SendingFacility>TEST_SENDING_FACILITY_1</SendingFacility><SendingExtract>PV</SendingExtract><Patient><PatientNumbers><PatientNumber><Number>888888888</Number><Organization>NHS</Organization><NumberType>NI</NumberType></PatientNumber></PatientNumbers><Names><Name use="L"><Family>NEWFAMILY</Family><Given>NEWGIVEN</Given></Name></Names><BirthTime>1985-01-01</BirthTime><Gender>9</Gender><Addresses><Address><Postcode>XX0 1TT</Postcode></Address></Addresses></Patient></ns0:PatientRecord>
    """.strip()
    )


def test_build_demographic_update_message_no_changes(ukrdc3_session):
    PID_1 = "PYTEST01:PV:00000000A"
    record = ukrdc3_session.query(PatientRecord).get(PID_1)

    message = build_demographic_update_message(
        record, name=None, birth_time=None, gender=None, address=None
    )

    assert (
        message
        == """
<?xml version="1.0" encoding="UTF-8"?>
<ns0:PatientRecord xmlns:ns0="http://www.rixg.org.uk/"><SendingFacility>TEST_SENDING_FACILITY_1</SendingFacility><SendingExtract>PV</SendingExtract><Patient><PatientNumbers><PatientNumber><Number>888888888</Number><Organization>NHS</Organization><NumberType>NI</NumberType></PatientNumber></PatientNumbers><Names><Name use="L"><Family>Star</Family><Given>Patrick</Given></Name></Names><BirthTime>1984-03-17</BirthTime><Gender>2</Gender></Patient></ns0:PatientRecord>
    """.strip()
    )


def test_build_demographic_update_message_full_address(ukrdc3_session):
    PID_1 = "PYTEST01:PV:00000000A"
    record = ukrdc3_session.query(PatientRecord).get(PID_1)

    message = build_demographic_update_message(
        record,
        name=None,
        birth_time=None,
        gender=None,
        address=AddressSchema(
            street="1 TEST STREET",
            town="TEST TOWN",
            county="TESTFORDSHIRE",
            postcode="XX0 1TT",
            country_code="GB",
            country_description="United Kingdom",
        ),
    )

    assert (
        message
        == """
<?xml version="1.0" encoding="UTF-8"?>
<ns0:PatientRecord xmlns:ns0="http://www.rixg.org.uk/"><SendingFacility>TEST_SENDING_FACILITY_1</SendingFacility><SendingExtract>PV</SendingExtract><Patient><PatientNumbers><PatientNumber><Number>888888888</Number><Organization>NHS</Organization><NumberType>NI</NumberType></PatientNumber></PatientNumbers><Names><Name use="L"><Family>Star</Family><Given>Patrick</Given></Name></Names><BirthTime>1984-03-17</BirthTime><Gender>2</Gender><Addresses><Address><Street>1 TEST STREET</Street><Town>TEST TOWN</Town><County>TESTFORDSHIRE</County><Postcode>XX0 1TT</Postcode><Country><CodingStandard>ISO3166-1</CodingStandard><Code>GB</Code><Description>United Kingdom</Description></Country></Address></Addresses></Patient></ns0:PatientRecord>
    """.strip()
    )
