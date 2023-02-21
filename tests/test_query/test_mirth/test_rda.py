import datetime

import pytest
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.query.mirth import rda
from ukrdc_fastapi.schemas.patient import AddressSchema, NameSchema


@pytest.mark.asyncio
async def test_create_pkb_membership(ukrdc3_session, redis_session, mirth_session):
    PID_1 = "PYTEST01:PV:00000000A"
    record = ukrdc3_session.query(PatientRecord).get(PID_1)

    response = await rda.update_patient_demographics(
        record,
        NameSchema(given="NEWGIVEN", family="NEWFAMILY"),
        datetime.datetime(1985, 1, 1),
        "9",
        AddressSchema(postcode="XX0 1TT"),
        mirth_session,
        redis_session,
    )
    assert response.status == "success"
    assert (
        response.message
        == """
<?xml version="1.0" encoding="UTF-8"?>
<ns0:PatientRecord xmlns:ns0="http://www.rixg.org.uk/"><SendingFacility>TSF01</SendingFacility><SendingExtract>UKRDC</SendingExtract><Patient><PatientNumbers><PatientNumber><Number>888888888</Number><Organization>NHS</Organization><NumberType>NI</NumberType></PatientNumber></PatientNumbers><Names><Name use="L"><Family>NEWFAMILY</Family><Given>NEWGIVEN</Given></Name></Names><BirthTime>1985-01-01T00:00:00</BirthTime><Gender>9</Gender><Addresses><Address><Postcode>XX0 1TT</Postcode></Address></Addresses></Patient></ns0:PatientRecord>
    """.strip()
    )
