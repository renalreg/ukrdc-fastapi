from fastapi import APIRouter
from starlette.responses import RedirectResponse

from . import (
    dashboard,
    empi,
    errors,
    facilities,
    laborders,
    masterrecords,
    mirth,
    patientrecords,
    persons,
    resultitems,
    search,
    user,
    workitems,
)

router = APIRouter()


@router.get("/", include_in_schema=False)
def root():
    """Redirect to documentation"""
    return RedirectResponse(url="./docs")


# Sub-resources
router.include_router(dashboard.router, prefix="/dash")
router.include_router(user.router, prefix="/user")
router.include_router(empi.router, prefix="/empi")
router.include_router(mirth.router, prefix="/mirth")

# Fuzzy-search
router.include_router(search.router, prefix="/search")

# UKRDC Records
router.include_router(facilities.router, prefix="/facilities")
router.include_router(patientrecords.router, prefix="/patientrecords")
router.include_router(laborders.router, prefix="/laborders")
router.include_router(errors.router, prefix="/errors")
router.include_router(resultitems.router, prefix="/resultitems")

# EMPI Records
router.include_router(workitems.router, prefix="/workitems")
router.include_router(persons.router, prefix="/persons")
router.include_router(masterrecords.router, prefix="/masterrecords")