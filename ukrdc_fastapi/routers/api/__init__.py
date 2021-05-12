from fastapi import APIRouter
from starlette.responses import RedirectResponse

from . import (
    dashboard,
    empi,
    errors,
    laborders,
    mirth,
    patientrecords,
    resultitems,
    user,
)

router = APIRouter()


@router.get("/", include_in_schema=False)
def root():
    """Redirect to documentation"""
    return RedirectResponse(url="./docs")


router.include_router(dashboard.router, prefix="/dash")
router.include_router(user.router, prefix="/user")
router.include_router(empi.router, prefix="/empi")
router.include_router(patientrecords.router, prefix="/patientrecords")
router.include_router(laborders.router, prefix="/laborders")
router.include_router(errors.router, prefix="/errors")
router.include_router(resultitems.router, prefix="/resultitems")
router.include_router(mirth.router, prefix="/mirth")
