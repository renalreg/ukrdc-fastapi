import json
from typing import Optional

from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import Code

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.schemas.facility import FacilitySchema


def get_facilities(
    ukrdc3: Session, redis: Redis, user: UKRDCUser
) -> list[FacilitySchema]:
    """Get a list of all unit/facility codes available to the current user

    Args:
        ukrdc3 (Session): SQLALchemy session
        redis (Redis): Redis session
        user (UKRDCUser): Logged-in user object

    Returns:
        list[FacilitySchema]: List of unit codes
    """
    redis_key: str = "ukrdc3:facilities"

    if not redis.exists(redis_key):
        codes = ukrdc3.query(Code).filter(Code.coding_standard == "RR1+")
        facilities = [
            FacilitySchema(id=code.code, description=code.description) for code in codes
        ]
        redis.set(redis_key, json.dumps([facility.dict() for facility in facilities]))
        # Cache for 12 hours
        redis.expire(redis_key, 43200)

    else:
        facilities_json: Optional[str] = redis.get(redis_key)
        if not facilities_json:
            facilities = []
        else:
            facilities = [
                FacilitySchema(**facility) for facility in json.loads(facilities_json)
            ]

    # Filter results by unit permissions
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD not in units:
        facilities = [facility for facility in facilities if facility.id in units]

    return facilities
