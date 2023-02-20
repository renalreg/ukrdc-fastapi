from fastapi import APIRouter, BackgroundTasks, Depends, Security
from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import PatientRecord

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
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.query.mirth.export import (
    export_all_to_pkb,
    export_all_to_pv,
    export_all_to_radar,
    export_docs_to_pv,
    export_tests_to_pv,
)
from ukrdc_fastapi.utils.tasks import TaskTracker, TrackableTaskSchema

from .dependencies import _get_patientrecord

router = APIRouter(tags=["Patient Records/Export"])


@router.post(
    "/pv",
    status_code=202,
    response_model=TrackableTaskSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv(
    background_tasks: BackgroundTasks,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
    tracker: TaskTracker = Depends(get_task_tracker),
):
    """Export a specific patient's data to PV"""
    task = tracker.http_create(
        export_all_to_pv,
        lock=f"task-export-pv-{patient_record.pid}",
        visibility="private",
        name=f"Export {patient_record.pid} to PV",
    )

    background_tasks.add_task(task.tracked, patient_record, mirth, redis)
    audit.add_event(
        Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.EXPORT_PV
    )

    return task.response()


@router.post(
    "/pv-tests",
    status_code=202,
    response_model=TrackableTaskSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv_tests(
    background_tasks: BackgroundTasks,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
    tracker: TaskTracker = Depends(get_task_tracker),
):
    """Export a specific patient's test data to PV"""
    task = tracker.http_create(
        export_tests_to_pv,
        lock=f"task-export-pv-tests-{patient_record.pid}",
        visibility="private",
        name=f"Export {patient_record.pid} tests to PV",
    )

    background_tasks.add_task(task.tracked, patient_record, mirth, redis)
    audit.add_event(
        Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.EXPORT_PV_TESTS
    )

    return task.response()


@router.post(
    "/pv-docs",
    status_code=202,
    response_model=TrackableTaskSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv_docs(
    background_tasks: BackgroundTasks,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
    tracker: TaskTracker = Depends(get_task_tracker),
):
    """Export a specific patient's documents data to PV"""
    task = tracker.http_create(
        export_docs_to_pv,
        lock=f"task-export-pv-docs-{patient_record.pid}",
        visibility="private",
        name=f"Export {patient_record.pid} documents to PV",
    )

    background_tasks.add_task(task.tracked, patient_record, mirth, redis)
    audit.add_event(
        Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.EXPORT_PV_DOCS
    )

    return task.response()


@router.post(
    "/radar",
    status_code=202,
    response_model=TrackableTaskSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_radar(
    background_tasks: BackgroundTasks,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
    tracker: TaskTracker = Depends(get_task_tracker),
):
    """Export a specific patient's data to RaDaR"""
    task = tracker.http_create(
        export_all_to_radar,
        lock=f"task-export-radar-{patient_record.pid}",
        visibility="private",
        name=f"Export {patient_record.pid} to RaDaR",
    )

    background_tasks.add_task(task.tracked, patient_record, mirth, redis)
    audit.add_event(
        Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.EXPORT_RADAR
    )

    return task.response()


@router.post(
    "/pkb",
    status_code=202,
    response_model=TrackableTaskSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pkb(
    background_tasks: BackgroundTasks,
    patient_record: PatientRecord = Depends(_get_patientrecord),
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
        lock=f"task-export-pkb-{patient_record.pid}",
        visibility="private",
        name=f"Export {patient_record.pid} to PKB",
    )

    background_tasks.add_task(task.tracked, patient_record, ukrdc3, mirth, redis)
    audit.add_event(
        Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.EXPORT_PKB
    )

    return task.response()
