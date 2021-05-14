from fastapi import APIRouter

from . import messages

router = APIRouter(tags=["Errors"])

router.include_router(messages.router, prefix="/messages")
