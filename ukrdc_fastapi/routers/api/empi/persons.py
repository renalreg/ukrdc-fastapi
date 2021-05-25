from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.masterrecords import get_masterrecords
from ukrdc_fastapi.query.persons import get_person, get_persons
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, PersonSchema
from ukrdc_fastapi.utils.links import find_related_ids
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


@router.get(
    "/",
    response_model=Page[PersonSchema],
    dependencies=[Security(auth.permission(Permissions.READ_EMPI))],
)
def persons(
    user: UKRDCUser = Security(auth.get_user), jtrace: Session = Depends(get_jtrace)
):
    """Retreive a list of person records from the EMPI"""
    return paginate(get_persons(jtrace, user))


@router.get(
    "/{person_id}/",
    response_model=PersonSchema,
    dependencies=[Security(auth.permission(Permissions.READ_EMPI))],
)
def person_detail(
    person_id: str,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a particular person record from the EMPI"""
    return get_person(jtrace, person_id, user)


@router.get(
    "/{person_id}/masterrecords/",
    response_model=list[MasterRecordSchema],
    dependencies=[Security(auth.permission(Permissions.READ_EMPI))],
)
def person_masterrecords(
    person_id: str,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a particular person record from the EMPI"""
    # Find all related master record IDs by recursing through link records
    related_master_ids, _ = find_related_ids(jtrace, set(), {person_id})
    return (
        get_masterrecords(jtrace, user)
        .filter(MasterRecord.id.in_(related_master_ids))
        .all()
    )
