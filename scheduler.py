from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_ERROR
from task_manager import get_pending_due_tasks, set_active_task, get_active_task_id
from whatsapp import send_whatsapp_message
import logging

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler()


def check_tasks():
    """
    Runs every 30 seconds.
    - Skips if there's already an active (unconfirmed) task.
    - Finds the next due pending task and sends a WhatsApp reminder.
    - Persists the active task ID to DB (survives restarts).
    """
    try:
        # Don't send a new reminder while one is still pending user response
        active_id = get_active_task_id()
        if active_id is not None:
            logger.debug(f"[Scheduler] Skipping — active task #{active_id} still pending")
            return

        due_tasks = get_pending_due_tasks()
        if not due_tasks:
            return

        task = due_tasks[0]  # process earliest due task first
        message = (
            f"⏰ Reminder: *{task['title']}*\n"
            f"Reply *done* when finished, or *snooze* for 10 more minutes."
        )

        sent = send_whatsapp_message(message)
        if sent:
            set_active_task(task["id"])
            logger.info(f"[Scheduler] Reminded task #{task['id']}: {task['title']}")
        else:
            logger.warning(f"[Scheduler] WhatsApp send failed for task #{task['id']}")

    except Exception as e:
        logger.error(f"[Scheduler] Unexpected error in check_tasks: {e}", exc_info=True)


def _on_job_error(event):
    logger.error(f"[Scheduler] Job crashed: {event.exception}")


def start_scheduler():
    if _scheduler.running:
        return
    _scheduler.add_listener(_on_job_error, EVENT_JOB_ERROR)
    _scheduler.add_job(check_tasks, "interval", seconds=30, id="check_tasks", replace_existing=True)
    _scheduler.start()
    logger.info("[Scheduler] Started — checking every 30 seconds")


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Stopped")
