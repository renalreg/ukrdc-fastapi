from fastapi import APIRouter

from . import pid

router = APIRouter(tags=["Patient Records"])
router.include_router(pid.router)
