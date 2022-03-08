import logging

import redis

from ukrdc_fastapi.config import settings


def clear_task_tracker() -> None:
    """Clear the task tracker"""
    print("clear_task_tracker")
    logging.info("Flushing tasks from task tracker")
    tasks_redis = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_tasks_db,
    )
    tasks_redis.flushdb()
    logging.info("Flushing locks from task tracker")
    locks_redis = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_locks_db,
    )
    locks_redis.flushdb()
