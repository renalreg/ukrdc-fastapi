import logging

from ukrdc_fastapi.dependencies import get_root_task_tracker


def clear_task_tracker() -> None:
    """Clear the task tracker"""
    tracker = get_root_task_tracker()
    logging.info("Flushing tasks from task tracker")
    tracker.task_redis.flushdb()
    logging.info("Flushing locks from task tracker")
    tracker.lock_redis.flushdb()
