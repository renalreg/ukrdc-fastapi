from fastapi import APIRouter

from . import record_id

router = APIRouter(tags=["Master Records"])
router.include_router(record_id.router)
