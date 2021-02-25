import datetime
from typing import Iterable, List, Optional, Set, Union

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Query as SqlQuery
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import or_
from sqlalchemy.sql.functions import concat

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.models.empi import LinkRecord, MasterRecord, Person, PidXRef
from ukrdc_fastapi.schemas.empi import PersonSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


def _ids_from_nhs_no(session: Session, nhs_nos: Iterable[str]):
    """Finds Ids from NHS number"""
    conditions = [MasterRecord.nationalid.like(nhs_no) for nhs_no in nhs_nos]
    matched_person_ids = set(
        [
            tup.person_id
            for tup in session.query(LinkRecord.person_id)
            .join(MasterRecord)
            .filter(
                or_(*conditions),
                MasterRecord.nationalid_type.in_(["NHS", "HSC", "CHI"]),
            )
            .all()
        ]
    )

    return matched_person_ids


def _ids_from_mrn_no(session: Session, mrn_nos: Iterable[str]):
    """Finds Ids from MRN number"""
    conditions = [PidXRef.localid.like(mrn_no) for mrn_no in mrn_nos]
    matched_person_ids = set(
        [
            tup.id
            for tup in session.query(Person.id)
            .join(PidXRef)
            .filter(or_(*conditions))
            .all()
        ]
    )

    return matched_person_ids


def _ids_from_ukrdc_no(session: Session, ukrdc_nos: Iterable[str]):
    """Finds Ids from UKRDC number"""
    conditions = [MasterRecord.nationalid.like(ukrdc_no) for ukrdc_no in ukrdc_nos]
    matched_person_ids = set(
        [
            tup.person_id
            for tup in session.query(LinkRecord.person_id)
            .join(MasterRecord)
            .filter(
                or_(*conditions),
                MasterRecord.nationalid_type.in_(["UKRDC"]),
            )
            .all()
        ]
    )

    return matched_person_ids


def _ids_from_full_name(session: Session, names: Iterable[str]):
    """Finds Ids from full name"""
    conditions = [
        concat(
            Person.givenname, " ", Person.other_given_names, " ", Person.surname
        ).like(name)
        for name in names
    ]
    matched_person_ids = set(
        [tup.id for tup in session.query(Person.id).filter(or_(*conditions)).all()]
    )

    return matched_person_ids


def _ids_from_dob(session: Session, dobs: Iterable[Union[str, datetime.date]]):
    """Finds Ids from date of birth"""
    conditions = [Person.date_of_birth.like(dob) for dob in dobs]
    matched_person_ids = set(
        [tup.id for tup in session.query(Person.id).filter(or_(*conditions)).all()]
    )

    return matched_person_ids


def _ids_from_pidxref_no(session: Session, pid_nos: Iterable[str]):
    """Finds Ids from pidxref"""
    conditions = [Person.localid.like(pid_no) for pid_no in pid_nos]
    matched_person_ids = set(
        [tup.id for tup in session.query(Person.id).filter(or_(*conditions)).all()]
    )

    return matched_person_ids


@router.get("/", response_model=Page[PersonSchema])
def search(
    nhs_number: Optional[List[str]] = Query(None),
    mrn_number: Optional[List[str]] = Query(None),
    ukrdc_number: Optional[List[str]] = Query(None),
    full_name: Optional[List[str]] = Query(None),
    dob: Optional[List[datetime.date]] = Query(None),
    pidx: Optional[List[str]] = Query(None),
    search: Optional[List[str]] = Query(None),
    jtrace: Session = Depends(get_jtrace),
):
    match_sets: List[Set[str]] = []

    nhs_number_list: List[str] = nhs_number or []
    mrn_number_list: List[str] = mrn_number or []
    ukrdc_number_list: List[str] = ukrdc_number or []
    full_name_list: List[str] = full_name or []
    dob_list: List[datetime.date] = dob or []
    pidx_list: List[str] = pidx or []
    search_list: List[str] = search or []

    if nhs_number or search_list:
        match_sets.append(_ids_from_nhs_no(jtrace, (*nhs_number_list, *search_list)))

    if mrn_number or search_list:
        match_sets.append(_ids_from_mrn_no(jtrace, (*mrn_number_list, *search_list)))

    if ukrdc_number or search_list:
        match_sets.append(
            _ids_from_ukrdc_no(jtrace, (*ukrdc_number_list, *search_list))
        )

    if full_name or search_list:
        match_sets.append(_ids_from_full_name(jtrace, (*full_name_list, *search_list)))

    if dob or search_list:
        match_sets.append(_ids_from_dob(jtrace, (*dob_list, *search_list)))

    if pidx or search_list:
        match_sets.append(_ids_from_pidxref_no(jtrace, (*pidx_list, *search_list)))

    non_empty_sets: List[Set[str]] = [
        match_set for match_set in match_sets if match_set
    ]

    matched_person_ids: Set[str] = set.intersection(*non_empty_sets)

    matched_persons: SqlQuery = jtrace.query(Person).filter(
        Person.id.in_(matched_person_ids)
    )

    return paginate(matched_persons)
