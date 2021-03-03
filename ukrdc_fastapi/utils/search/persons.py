import datetime
from typing import Iterable, Union

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import or_
from sqlalchemy.sql.functions import concat

from ukrdc_fastapi.models.empi import LinkRecord, MasterRecord, Person, PidXRef


def person_ids_from_nhs_no(session: Session, nhs_nos: Iterable[str]):
    """Finds Ids from NHS number"""
    conditions = [MasterRecord.nationalid.like(nhs_no) for nhs_no in nhs_nos]
    matched_person_ids = {
        tup.person_id
        for tup in session.query(LinkRecord.person_id)
        .join(MasterRecord)
        .filter(
            or_(*conditions),
            MasterRecord.nationalid_type.in_(["NHS", "HSC", "CHI"]),
        )
        .all()
    }

    return matched_person_ids


def person_ids_from_mrn_no(session: Session, mrn_nos: Iterable[str]):
    """Finds Ids from MRN number"""
    conditions = [PidXRef.localid.like(mrn_no) for mrn_no in mrn_nos]
    matched_person_ids = {
        tup.id
        for tup in session.query(Person.id).join(PidXRef).filter(or_(*conditions)).all()
    }

    return matched_person_ids


def person_ids_from_ukrdc_no(session: Session, ukrdc_nos: Iterable[str]):
    """Finds Ids from UKRDC number"""
    conditions = [MasterRecord.nationalid.like(ukrdc_no) for ukrdc_no in ukrdc_nos]
    matched_person_ids = {
        tup.person_id
        for tup in session.query(LinkRecord.person_id)
        .join(MasterRecord)
        .filter(
            or_(*conditions),
            MasterRecord.nationalid_type.in_(["UKRDC"]),
        )
        .all()
    }

    return matched_person_ids


def person_ids_from_full_name(session: Session, names: Iterable[str]):
    """Finds Ids from full name"""
    conditions = []
    conditions += [
        concat(
            Person.givenname, " ", Person.other_given_names, " ", Person.surname
        ).like(name)
        for name in names
    ]
    conditions += [Person.givenname.ilike(name) for name in names]
    conditions += [Person.other_given_names.ilike(name) for name in names]
    conditions += [Person.surname.ilike(name) for name in names]
    matched_person_ids = {
        tup.id for tup in session.query(Person.id).filter(or_(*conditions)).all()
    }

    return matched_person_ids


def person_ids_from_dob(session: Session, dobs: Iterable[Union[str, datetime.date]]):
    """Finds Ids from date of birth"""
    conditions = [Person.date_of_birth == dob for dob in dobs]
    matched_person_ids = {
        tup.id for tup in session.query(Person.id).filter(or_(*conditions)).all()
    }

    return matched_person_ids


def person_ids_from_pidxref_no(session: Session, pid_nos: Iterable[str]):
    """Finds Ids from pidxref"""
    conditions = [Person.localid.like(pid_no) for pid_no in pid_nos]
    matched_person_ids = {
        tup.id for tup in session.query(Person.id).filter(or_(*conditions)).all()
    }

    return matched_person_ids
