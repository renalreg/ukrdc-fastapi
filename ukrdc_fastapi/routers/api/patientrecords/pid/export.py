from fastapi import APIRouter, BackgroundTasks, Depends, Security
from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import (
    get_mirth,
    get_redis,
    get_task_tracker,
    get_ukrdc3,
)
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    RecordOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.mirth.export import (
    export_all_to_pkb,
    export_all_to_pv,
    export_all_to_radar,
    export_docs_to_pv,
    export_tests_to_pv,
)
from ukrdc_fastapi.tasks.background import TaskTracker, TrackableTaskSchema

router = APIRouter(tags=["Patient Records/Export"])


@router.post(
    "/pv",
    status_code=202,
    response_model=TrackableTaskSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv(
    pid: str,
    background_tasks: BackgroundTasks,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
    tracker: TaskTracker = Depends(get_task_tracker),
):
    """Export a specific patient's data to PV"""
    task = tracker.http_create(
        export_all_to_pv,
        lock=f"task-export-pv-{pid}",
        visibility="private",
        name=f"Export {pid} to PV",
    )

    background_tasks.add_task(task.tracked, pid, user, ukrdc3, mirth, redis)
    audit.add_event(Resource.PATIENT_RECORD, pid, RecordOperation.EXPORT_PV)

    return task.response()


@router.post(
    "/pv-tests",
    status_code=202,
    response_model=TrackableTaskSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv_tests(
    pid: str,
    background_tasks: BackgroundTasks,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
    tracker: TaskTracker = Depends(get_task_tracker),
):
    """Export a specific patient's test data to PV"""
    task = tracker.http_create(
        export_tests_to_pv,
        lock=f"task-export-pv-tests-{pid}",
        visibility="private",
        name=f"Export {pid} tests to PV",
    )

    background_tasks.add_task(task.tracked, pid, user, ukrdc3, mirth, redis)
    audit.add_event(Resource.PATIENT_RECORD, pid, RecordOperation.EXPORT_PV_TESTS)

    return task.response()


@router.post(
    "/pv-docs",
    status_code=202,
    response_model=TrackableTaskSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv_docs(
    pid: str,
    background_tasks: BackgroundTasks,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
    tracker: TaskTracker = Depends(get_task_tracker),
):
    """Export a specific patient's documents data to PV"""
    task = tracker.http_create(
        export_docs_to_pv,
        lock=f"task-export-pv-docs-{pid}",
        visibility="private",
        name=f"Export {pid} documents to PV",
    )

    background_tasks.add_task(task.tracked, pid, user, ukrdc3, mirth, redis)
    audit.add_event(Resource.PATIENT_RECORD, pid, RecordOperation.EXPORT_PV_DOCS)

    return task.response()


@router.post(
    "/radar",
    status_code=202,
    response_model=TrackableTaskSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_radar(
    pid: str,
    background_tasks: BackgroundTasks,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
    tracker: TaskTracker = Depends(get_task_tracker),
):
    """Export a specific patient's data to RaDaR"""
    task = tracker.http_create(
        export_all_to_radar,
        lock=f"task-export-radar-{pid}",
        visibility="private",
        name=f"Export {pid} to RaDaR",
    )

    background_tasks.add_task(task.tracked, pid, user, ukrdc3, mirth, redis)
    audit.add_event(Resource.PATIENT_RECORD, pid, RecordOperation.EXPORT_RADAR)

    return task.response()


@router.post(
    "/pkb",
    status_code=202,
    response_model=TrackableTaskSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pkb(
    pid: str,
    background_tasks: BackgroundTasks,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
    tracker: TaskTracker = Depends(get_task_tracker),
):
    """
    Export a specific patient's data to PKB.
    This export runs as a background task since the split sending can take a while.
    """
    task = tracker.http_create(
        export_all_to_pkb,
        lock=f"task-export-pkb-{pid}",
        visibility="private",
        name=f"Export {pid} to PKB",
    )

    background_tasks.add_task(task.tracked, pid, user, ukrdc3, mirth, redis)
    audit.add_event(Resource.PATIENT_RECORD, pid, RecordOperation.EXPORT_PKB)

    return task.response()
