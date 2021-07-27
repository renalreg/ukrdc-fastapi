from fastapi import APIRouter, Depends, HTTPException, Security
from httpx import Response
from mirth_client.mirth import MirthAPI
from redis import Redis

from ukrdc_fastapi.dependencies import get_mirth, get_redis
from ukrdc_fastapi.dependencies.auth import auth
from ukrdc_fastapi.utils.mirth import (
    MirthMessageResponseSchema,
    build_export_all_message,
    build_export_docs_message,
    build_export_radar_message,
    build_export_tests_message,
    get_channel_from_name,
)

router = APIRouter(tags=["Patient Records/Export"])


@router.post(
    "/pv/",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(auth.permissions.EXPORT_RECORDS))],
)
async def patient_export_pv(
    pid: str, mirth: MirthAPI = Depends(get_mirth), redis: Redis = Depends(get_redis)
):
    """Export a specific patient's data to PV"""
    channel = get_channel_from_name("PV Outbound", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for PV Outbound channel not found"
        )  # pragma: no cover

    message: str = build_export_all_message(pid)

    response: Response = await channel.post_message(message)

    if response.status_code >= 400:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


@router.post(
    "/pv-tests/",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(auth.permissions.EXPORT_RECORDS))],
)
async def patient_export_pv_tests(
    pid: str, mirth: MirthAPI = Depends(get_mirth), redis: Redis = Depends(get_redis)
):
    """Export a specific patient's test data to PV"""
    channel = get_channel_from_name("PV Outbound", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for PV Outbound channel not found"
        )  # pragma: no cover

    message: str = build_export_tests_message(pid)

    response: Response = await channel.post_message(message)

    if response.status_code >= 400:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


@router.post(
    "/pv-docs/",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(auth.permissions.EXPORT_RECORDS))],
)
async def patient_export_pv_docs(
    pid: str, mirth: MirthAPI = Depends(get_mirth), redis: Redis = Depends(get_redis)
):
    """Export a specific patient's documents data to PV"""
    channel = get_channel_from_name("PV Outbound", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for PV Outbound channel not found"
        )  # pragma: no cover

    message: str = build_export_docs_message(pid)

    response: Response = await channel.post_message(message)

    if response.status_code >= 400:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


@router.post(
    "/radar/",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(auth.permissions.EXPORT_RECORDS))],
)
async def patient_export_radar(
    pid: str, mirth: MirthAPI = Depends(get_mirth), redis: Redis = Depends(get_redis)
):
    """Export a specific patient's data to RaDaR"""
    channel = get_channel_from_name("RADAR Outbound", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for RADAR Outbound channel not found"
        )  # pragma: no cover

    message: str = build_export_radar_message(pid)

    response: Response = await channel.post_message(message)

    if response.status_code >= 400:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)
