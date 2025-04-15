from fastapi import APIRouter, Depends, Security
from mirth_client import MirthAPI
from redis import Redis
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_mirth, get_redis, get_ukrdc3
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.exceptions import PermissionsError
from ukrdc_fastapi.permissions.patientrecords import apply_patientrecord_list_permission
from ukrdc_fastapi.query.mirth.memberships import create_partner_membership_for_ukrdcid
from ukrdc_fastapi.query.patientrecords import select_patientrecords_related_to_ukrdcid
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSummarySchema
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema

router = APIRouter(tags=["UKRDC Record Group"])


@router.get(
    "/{ukrdcid}/records",
    response_model=list[PatientRecordSummarySchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def ukrdcid_records(
    ukrdcid: str,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive patient records related to a specific patient record"""
    stmt = select_patientrecords_related_to_ukrdcid(ukrdcid)
    stmt = apply_patientrecord_list_permission(stmt, user)

    related = ukrdc3.scalars(stmt).all()

    record_audit = audit.add_event(Resource.UKRDCID, ukrdcid, AuditOperation.READ)
    for record in related:
        audit.add_event(
            Resource.PATIENT_RECORD,
            record.pid,
            AuditOperation.READ,
            parent=record_audit,
        )

    return related


@router.post(
    "/{ukrdcid}/memberships/create/pkb",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(Permissions.CREATE_MEMBERSHIPS))],
)
async def ukrdcid_memberships_create_pkb(
    ukrdcid: str,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    mirth: MirthAPI = Depends(get_mirth),
    audit: Auditer = Depends(get_auditer),
    redis: Redis = Depends(get_redis),
):
    """
    Create a new membership for a master record.
    """

    return await create_partner_membership(
        ukrdcid=ukrdcid,
        user=user,
        ukrdc3=ukrdc3,
        mirth=mirth,
        audit=audit,
        redis=redis,
        partner="PKB",
    )


@router.post(
    "/{ukrdcid}/memberships/create/mrc",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(Permissions.CREATE_MEMBERSHIPS))],
)
async def ukrdcid_memberships_create_mrc(
    ukrdcid: str,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    mirth: MirthAPI = Depends(get_mirth),
    audit: Auditer = Depends(get_auditer),
    redis: Redis = Depends(get_redis),
):
    return await create_partner_membership(
        ukrdcid=ukrdcid,
        user=user,
        ukrdc3=ukrdc3,
        mirth=mirth,
        audit=audit,
        redis=redis,
        partner="MRC",
    )


# TODO: Move this to a separate file
async def create_partner_membership(
    ukrdcid: str,
    user: UKRDCUser,
    ukrdc3: Session,
    mirth: MirthAPI,
    audit: Auditer,
    redis: Redis,
    partner: str,
) -> MirthMessageResponseSchema:
    """
    Create a new membership for a master record.
    """

    # Find related records the user has permission to access
    stmt = select_patientrecords_related_to_ukrdcid(ukrdcid)
    stmt = apply_patientrecord_list_permission(stmt, user)
    records = ukrdc3.scalars(stmt).all()

    # If the user doesn't have access to any related records, raise a permission error
    if len(records) == 0:
        raise PermissionsError()

    audit.add_event(
        Resource.MEMBERSHIP,
        partner,
        AuditOperation.CREATE,
        parent=audit.add_event(Resource.UKRDCID, ukrdcid, AuditOperation.READ),
    )

    return await create_partner_membership_for_ukrdcid(ukrdcid, mirth, redis, partner)
