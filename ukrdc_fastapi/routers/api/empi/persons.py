from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Query as OrmQuery
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord, Person

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.auth import Auth0User, Scopes, Security, auth
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, PersonSchema
from ukrdc_fastapi.utils.filters import find_ids_related_to_person
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


@router.get("/", response_model=Page[PersonSchema])
def persons(
    clpid: Optional[list[str]] = Query(None),
    jtrace: Session = Depends(get_jtrace),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_EMPI]),
):
    """Retreive a list of person records from the EMPI"""
    people: OrmQuery = jtrace.query(Person)
    if clpid:
        people = people.filter(Person.localid.in_(clpid))
    return paginate(people)


@router.get("/{person_id}/", response_model=PersonSchema)
def person_detail(
    person_id: str,
    jtrace: Session = Depends(get_jtrace),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_EMPI]),
):
    """Retreive a particular person record from the EMPI"""
    person = jtrace.query(Person).get(person_id)
    if not person:
        raise HTTPException(404, detail="EMPI Person not found")
    return person


@router.get("/{person_id}/masterrecords/", response_model=list[MasterRecordSchema])
def person_masterrecords(
    person_id: str,
    jtrace: Session = Depends(get_jtrace),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_EMPI]),
):
    """Retreive a particular person record from the EMPI"""
    person = jtrace.query(Person).get(person_id)
    if not person:
        raise HTTPException(404, detail="EMPI Person not found")

    related_masterrecord_ids, _ = find_ids_related_to_person([person.localid], jtrace)

    masterrecords: OrmQuery = jtrace.query(MasterRecord).filter(
        MasterRecord.id.in_(related_masterrecord_ids)
    )

    return masterrecords.all()
