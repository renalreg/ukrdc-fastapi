import datetime
from typing import Optional

from sqlalchemy.orm import Session
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person, PidXRef
from ukrdc_sqla.ukrdc import (
    Address,
    Code,
    Facility,
    Name,
    Patient,
    PatientNumber,
    PatientRecord,
)


def days_ago(days: int):
    dt = datetime.datetime.now() - datetime.timedelta(days=days)
    # Strip time from datetime
    return datetime.datetime(year=dt.year, month=dt.month, day=dt.day)


def create_basic_patient(
    id_: int,
    pid: str,
    ukrdcid: str,
    nhs_number: str,
    sendingfacility: str,
    sendingextract: str,
    localpatientid: str,
    family_name: str,
    given_name: str,
    birth_time: datetime,
    ukrdc3: Session,
    jtrace: Session,
):
    record = PatientRecord(
        pid=pid,
        sendingfacility=sendingfacility,
        sendingextract=sendingextract,
        localpatientid=localpatientid,
        ukrdcid=ukrdcid,
        repository_update_date=datetime.datetime(2020, 3, 16),
        repository_creation_date=datetime.datetime(2020, 3, 16),
    )

    name = Name(id=id_, pid=pid, family=family_name, given=given_name, nameuse="L")
    address = Address(
        id=f"ADDRESS{id_}",
        pid=pid,
        street=f"12{id_} Conch Street",
        town="Bikini Bottom",
        county="Bikini County",
        postcode="XX0 1AA",
        country_description="Pacific Ocean",
    )

    patient = Patient(
        pid=pid,
        birth_time=birth_time,
        gender=f"{id_%2 + 1}",
        ethnic_group_code="G",
        ethnic_group_description="ETHNICITY_GROUP",
    )
    patient_number = PatientNumber(
        id=id_, pid=pid, patientid=nhs_number, organization="NHS", numbertype="NI"
    )

    ukrdc3.add(record)
    ukrdc3.add(name)
    ukrdc3.add(address)
    ukrdc3.add(patient)
    ukrdc3.add(patient_number)

    master_record_ukrdc = MasterRecord(
        id=id_,
        status=0,
        last_updated=datetime.datetime(2020, 3, 16),
        givenname=given_name,
        surname=family_name,
        date_of_birth=birth_time,
        nationalid=ukrdcid,
        nationalid_type="UKRDC",
        effective_date=datetime.datetime(2020, 3, 16),
    )

    master_record_nhs = MasterRecord(
        id=id_ + 100,
        status=0,
        last_updated=datetime.datetime(2020, 3, 16),
        givenname=given_name,
        surname=family_name,
        date_of_birth=birth_time,
        nationalid=nhs_number,
        nationalid_type="NHS",
        effective_date=datetime.datetime(2020, 3, 16),
    )

    person = Person(
        id=id_,
        originator="UKRDC",
        localid=pid,
        localid_type="CLPID",
        date_of_birth=birth_time,
        gender=f"{id_%2 + 1}",
    )

    xref = PidXRef(
        id=id_,
        pid=pid,
        sending_facility=sendingfacility,
        sending_extract=sendingextract,
        localid=f"XREF_LOCALID_{id_}",
    )

    link_record_ukrdc = LinkRecord(
        id=id_,
        person_id=id_,
        master_id=id_,
        link_type=0,
        link_code=0,
        last_updated=datetime.datetime(2019, 1, 1),
    )

    link_record_nhs = LinkRecord(
        id=id_ + 100,
        person_id=id_,
        master_id=id_ + 100,
        link_type=0,
        link_code=0,
        last_updated=datetime.datetime(2019, 1, 1),
    )

    jtrace.add(master_record_ukrdc)
    jtrace.add(master_record_nhs)
    jtrace.add(person)
    jtrace.add(xref)
    jtrace.add(link_record_ukrdc)
    jtrace.add(link_record_nhs)

    ukrdc3.commit()
    jtrace.commit()


def create_basic_facility(
    code: str,
    description: str,
    ukrdc3: Session,
    pkb_in: bool = False,
    pkb_out: bool = False,
    pkb_msg_exclusions: Optional[list[str]] = None,
):
    code_obj = Code(
        coding_standard="RR1+",
        code=code,
        description=description,
        creation_date=datetime.datetime(2020, 3, 16),
    )

    facility_obj = Facility(
        code=code,
        pkb_in=pkb_in,
        pkb_out=pkb_out,
        pkb_msg_exclusions=pkb_msg_exclusions if pkb_msg_exclusions else [],
    )

    ukrdc3.add(code_obj)
    ukrdc3.add(facility_obj)

    ukrdc3.commit()
