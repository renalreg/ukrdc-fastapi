import json
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import Code

from ukrdc_fastapi.dependencies import get_redis, get_ukrdc3

router = APIRouter(tags=["Facilities"])


class FacilitySchema(BaseModel):
    id: str
    description: Optional[str]


@router.get("/", response_model=list[FacilitySchema])
def facility_list(
    ukrdc3: Session = Depends(get_ukrdc3), redis: Redis = Depends(get_redis)
):
    """Retreive a list of on-record facilities"""
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

    return facilities
