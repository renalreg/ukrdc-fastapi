from fastapi import APIRouter
from starlette.responses import RedirectResponse

from . import (
    admin,
    codes,
    dashboard,
    empi,
    facilities,
    masterrecords,
    messages,
    mirth,
    patientrecords,
    persons,
    search,
    system,
    tasks,
    workitems,
)

router = APIRouter()


@router.get("", include_in_schema=False)
def root():
    """Redirect to documentation"""
    return RedirectResponse(url="./docs")


# Sub-resources
router.include_router(admin.router, prefix="/admin")
router.include_router(dashboard.router, prefix="/dash")
router.include_router(system.router, prefix="/system")
router.include_router(empi.router, prefix="/empi")
router.include_router(mirth.router, prefix="/mirth")

# Fuzzy-search
router.include_router(search.router, prefix="/search")

# UKRDC Records
router.include_router(patientrecords.router, prefix="/patientrecords")
router.include_router(facilities.router, prefix="/facilities")
router.include_router(codes.router, prefix="/codes")

# EMPI Records
router.include_router(workitems.router, prefix="/workitems")
router.include_router(persons.router, prefix="/persons")
router.include_router(masterrecords.router, prefix="/masterrecords")

# ErrorsDB/Message Records
router.include_router(messages.router, prefix="/messages")

# Task management
router.include_router(tasks.router, prefix="/tasks")
