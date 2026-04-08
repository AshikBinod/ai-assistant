from database import get_db
from models import Task, ActiveTask
from datetime import datetime


# ─── TASK CRUD ────────────────────────────────────────────────────────────────

def create_task(title: str, scheduled_time: datetime) -> dict:
    with get_db() as db:
        task = Task(title=title, scheduled_time=scheduled_time, status="pending")
        db.add(task)
        db.flush()  # get the id before closing
        return task.to_dict()


def get_tasks(status: str = None) -> list[dict]:
    """Return tasks as plain dicts (safe after session closes)."""
    with get_db() as db:
        query = db.query(Task)
        if status:
            query = query.filter(Task.status == status)
        return [t.to_dict() for t in query.order_by(Task.scheduled_time).all()]


def get_pending_due_tasks() -> list[dict]:
    """Return pending tasks whose scheduled_time has passed."""
    with get_db() as db:
        now = datetime.now()
        tasks = (
            db.query(Task)
            .filter(Task.status == "pending", Task.scheduled_time <= now)
            .order_by(Task.scheduled_time)
            .all()
        )
        return [t.to_dict() for t in tasks]


def complete_task(task_id: int) -> bool:
    """Mark a task completed. Returns True if found, False if not."""
    with get_db() as db:
        task = db.get(Task, task_id)  # modern SQLAlchemy 2.x syntax
        if not task:
            return False
        task.status = "completed"
        return True


def snooze_task(task_id: int, minutes: int = 10) -> bool:
    """Push a task's scheduled_time forward by N minutes."""
    from datetime import timedelta
    with get_db() as db:
        task = db.get(Task, task_id)
        if not task:
            return False
        task.scheduled_time = datetime.now() + timedelta(minutes=minutes)
        task.status = "pending"
        return True


# ─── ACTIVE TASK (REPLACES in-memory last_task_id) ───────────────────────────

def set_active_task(task_id: int):
    """Persist the currently-reminded task to DB (survives restarts)."""
    with get_db() as db:
        record = db.get(ActiveTask, 1)
        if record:
            record.task_id = task_id
            record.reminded_at = datetime.now()
        else:
            db.add(ActiveTask(id=1, task_id=task_id, reminded_at=datetime.now()))


def get_active_task_id() -> int | None:
    """Retrieve the currently active task ID from DB."""
    with get_db() as db:
        record = db.get(ActiveTask, 1)
        return record.task_id if record else None


def clear_active_task():
    """Clear the active task (after completion or snooze)."""
    with get_db() as db:
        record = db.get(ActiveTask, 1)
        if record:
            record.task_id = None
