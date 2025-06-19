import datetime
from typing import Optional

from ukrdc_sqla.ukrdc import PatientRecord
from ukrdc_xsdata.ukrdc import Patient as RDAPatient,PatientRecord as RDAPatientRecord,types  #type: ignore
from xsdata.formats.dataclass.serializers.xml import XmlSerializer
from xsdata.models.datatype import XmlDate, XmlDateTime

from ukrdc_fastapi.schemas.patientrecord.patient import (
    AddressSchema,
    GenderType,
    NameSchema,
)


def build_demographic_update_message(
    record: PatientRecord,
    name: Optional[NameSchema],
    birth_time: Optional[datetime.datetime],
    gender: Optional[GenderType],
    address: Optional[AddressSchema],
) -> str:
    """
    Build an RDA XML message to update the demographic data of a given patient record

    Args:
        record (PatientRecord): Base patient record to update
        name (Optional[NameSchema]): New name to set
        birth_time (Optional[datetime.date]): New date of birth to set
        gender (Optional[GenderType]): New gender code to set
        address (Optional[AddressSchema]): New address to set

    Returns:
        str: RDA XML string
    """
    # Build imutable section of the message (i.e. record parameters we don't allow to change)
    patient_numbers = [
        types.PatientNumber(
            number=number.patientid,
            organization=number.organization,
            number_type=number.numbertype,
        )
        for number in record.patient.numbers
    ]

    # Build new values
    new_address = (
        types.Address(
            from_time=XmlDate.from_date(address.from_time)
            if address.from_time
            else None,
            to_time=XmlDate.from_date(address.to_time) if address.to_time else None,
            street=address.street,
            town=address.town,
            county=address.county,
            postcode=address.postcode,
            country=types.Address.Country(
                coding_standard=address.country_code_std or "ISO3166-1",
                code=address.country_code,
                description=address.country_description,
            )
            # Skip country object if all country fields are empty
            if (
                address.country_code_std
                or address.country_code
                or address.country_description
            )
            else None,
        )
        # RDA feeds can have empty address objects
        if address
        else None
    )

    new_names: RDAPatient.Names = (
        RDAPatient.Names(
            name=[types.Name(use="L", family=name.family, given=name.given)]
        )
        # RDA feeds require a name, so if none is provided, use the existing one
        if name
        else RDAPatient.Names(
            name=[
                types.Name(
                    use=record.patient.names[0].nameuse,
                    family=record.patient.names[0].family,
                    given=record.patient.names[0].given,
                )
            ]
        )
    )

    new_birth_time = birth_time or record.patient.birth_time

    # Build RDA message
    rda_record = RDAPatientRecord(
        sending_facility=record.sendingfacility,
        sending_extract=record.sendingextract,
        patient=RDAPatient(
            birth_time=XmlDateTime.from_datetime(new_birth_time)
            if new_birth_time
            else None,
            gender=gender or record.patient.gender,
            names=new_names,
            addresses=RDAPatient.Addresses(address=[new_address])
            if new_address
            else None,
            patient_numbers=types.PatientNumbers(patient_number=patient_numbers),
        ),
    )

    return XmlSerializer().render(rda_record)
