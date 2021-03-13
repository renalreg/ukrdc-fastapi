from fastapi import APIRouter

from . import linkrecords, masterrecords, persons, search, workitems

router = APIRouter()

router.include_router(workitems.router, prefix="/workitems")
router.include_router(linkrecords.router, prefix="/linkrecords")
router.include_router(persons.router, prefix="/persons")
router.include_router(masterrecords.router, prefix="/masterrecords")
router.include_router(search.router, prefix="/search")
