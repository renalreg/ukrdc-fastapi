from ukrdc_fastapi.config import configuration


async def test_record_export_data(client):
    demographics = {
        "name": {
            "family": "NEWFAMILY",
            "given": "NEWGIVEN",
        },
        "birth_time": "1985-01-01T00:00:00",
        "gender": "9",
        "address": {
            "street": "1 TEST STREET",
            "town": "TEST TOWN",
            "county": "TESTFORDSHIRE",
            "postcode": "XX0 1TT",
            "country_code": "GB",
            "country_description": "United Kingdom",
        },
    }
    response = await client.post(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/update/demographics",
        json=demographics,
    )

    assert response.status_code == 200
    assert (
        response.json().get("message")
        == """
<?xml version="1.0" encoding="UTF-8"?>
<ns0:PatientRecord xmlns:ns0="http://www.rixg.org.uk/"><SendingFacility>TEST_SENDING_FACILITY_1</SendingFacility><SendingExtract>UKRDC</SendingExtract><Patient><PatientNumbers><PatientNumber><Number>888888888</Number><Organization>NHS</Organization><NumberType>NI</NumberType></PatientNumber></PatientNumbers><Names><Name use="L"><Family>NEWFAMILY</Family><Given>NEWGIVEN</Given></Name></Names><BirthTime>1985-01-01T00:00:00</BirthTime><Gender>9</Gender><Addresses><Address><Street>1 TEST STREET</Street><Town>TEST TOWN</Town><County>TESTFORDSHIRE</County><Postcode>XX0 1TT</Postcode><Country><CodingStandard>ISO3166-1</CodingStandard><Code>GB</Code><Description>United Kingdom</Description></Country></Address></Addresses></Patient></ns0:PatientRecord>
    """.strip()
    )
