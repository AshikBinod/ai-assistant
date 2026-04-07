from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from task_manager import get_tasks
from whatsapp import send_whatsapp_message

scheduler = BackgroundScheduler()

# 🔥 Persistent state
last_task_id = None

def check_tasks():
    global last_task_id

    tasks = get_tasks()
    now = datetime.now()

    # 🔥 ONLY assign if no active task
    if last_task_id is not None:
        return

    for task in tasks:
        if task.status == "pending" and task.scheduled_time <= now:
            message = f"⏰ Reminder: {task.title}"
            print(message)

            send_whatsapp_message(message)

            # 🔥 SET ONLY ONCE
            last_task_id = task.id
            print("Set last_task_id:", last_task_id)

            break  # 🔥 IMPORTANT: stop after first match

def start_scheduler():
    scheduler.add_job(check_tasks, "interval", seconds=30)
    scheduler.start()