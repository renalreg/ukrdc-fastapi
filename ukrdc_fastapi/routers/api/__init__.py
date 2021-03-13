from fastapi import APIRouter
from starlette.responses import RedirectResponse

from ukrdc_fastapi.config import settings

from . import dashboard, empi, errors, laborders, patientrecords, resultitems

router = APIRouter()


@router.get("/", include_in_schema=False)
def root():
    """Redirect to documentation"""
    return RedirectResponse(url="./docs")


router.include_router(
    dashboard.router,
    prefix="/dash",
    tags=["Summary Dashboard"],
)
router.include_router(
    empi.router,
    prefix="/empi",
    tags=["Master-Patient Index"],
)
router.include_router(
    patientrecords.router,
    prefix="/patientrecords",
    tags=["Patient Records"],
)
router.include_router(
    laborders.router,
    prefix="/laborders",
    tags=["Lab Orders"],
)
router.include_router(
    errors.router,
    prefix="/errors",
    tags=["Errors"],
)
router.include_router(
    resultitems.router,
    prefix="/resultitems",
    tags=["Result Items"],
)
