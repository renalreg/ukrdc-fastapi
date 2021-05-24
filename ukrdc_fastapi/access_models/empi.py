from fastapi import HTTPException
from sqlalchemy.orm import Query
from ukrdc_sqla import empi

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser


class MasterRecordAM(empi.MasterRecord):
    @classmethod
    def apply_query_permissions(cls, query: Query, user: UKRDCUser):
        units = Permissions.unit_codes(user.permissions)
        if Permissions.UNIT_WILDCARD in units:
            return query

        return (
            query.join(empi.LinkRecord)
            .join(empi.Person)
            .join(empi.PidXRef)
            .filter(empi.PidXRef.sending_facility.in_(units))
        )

    @classmethod
    def assert_permission(cls, record: empi.MasterRecord, user: UKRDCUser):
        units = Permissions.unit_codes(user.permissions)
        if Permissions.UNIT_WILDCARD in units:
            return

        link: empi.LinkRecord
        for link in record.link_records:
            person: empi.Person = link.person
            xref: empi.PidXRef
            for xref in person.xref_entries:
                if xref.sending_facility in units:
                    return

        raise HTTPException(
            403,
            detail=f"You do not have permission to access this resource. Sending facility does not match.",
        )


class PersonAM:
    @classmethod
    def apply_query_permissions(cls, query: Query, user: UKRDCUser):
        units = Permissions.unit_codes(user.permissions)
        if Permissions.UNIT_WILDCARD in units:
            return query

        return query.join(empi.PidXRef).filter(empi.PidXRef.sending_facility.in_(units))

    @classmethod
    def assert_permission(cls, person: empi.Person, user: UKRDCUser):
        units = Permissions.unit_codes(user.permissions)
        if Permissions.UNIT_WILDCARD in units:
            return

        xref: empi.PidXRef
        for xref in person.xref_entries:
            if xref.sending_facility in units:
                return

        raise HTTPException(
            403,
            detail="You do not have permission to access this resource. Sending facility does not match.",
        )


class WorkItemAM:
    @classmethod
    def apply_query_permissions(cls, query: Query, user: UKRDCUser):
        units = Permissions.unit_codes(user.permissions)
        if Permissions.UNIT_WILDCARD in units:
            return query

        return (
            query.join(empi.Person)
            .join(empi.PidXRef)
            .filter(empi.PidXRef.sending_facility.in_(units))
        )

    @classmethod
    def assert_permission(cls, workitem: empi.WorkItem, user: UKRDCUser):
        units = Permissions.unit_codes(user.permissions)
        if Permissions.UNIT_WILDCARD in units:
            return

        person: empi.Person = workitem.person
        xref: empi.PidXRef
        for xref in person.xref_entries:
            if xref.sending_facility in units:
                return

        raise HTTPException(
            403,
            detail="You do not have permission to access this resource. Sending facility does not match.",
        )
