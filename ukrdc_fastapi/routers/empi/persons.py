from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Query, Session

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.models.empi import Person
from ukrdc_fastapi.schemas.empi import PersonSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


@router.get("/", response_model=Page[PersonSchema])
def persons(ni: Optional[str] = None, jtrace: Session = Depends(get_jtrace)):
    persons: Query = jtrace.query(Person)
    if ni:
        persons = persons.filter(Person.nationalid == ni)
    return paginate(persons)


@router.get("/{person_id}", response_model=PersonSchema)
def person_detail(person_id: str, jtrace: Session = Depends(get_jtrace)):
    person = jtrace.query(Person).get(person_id)
    if not person:
        raise HTTPException(404, detail="EMPI Person not found")
    return person
