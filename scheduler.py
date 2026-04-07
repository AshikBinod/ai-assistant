from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from task_manager import get_tasks
from whatsapp import send_whatsapp_message

scheduler = BackgroundScheduler()

# 🔥 Shared state
last_task_id = None

def check_tasks():
    global last_task_id

    tasks = get_tasks()
    now = datetime.now()

    for task in tasks:
        if task.status == "pending" and task.scheduled_time <= now:
            message = f"⏰ Reminder: {task.title}"
            print(message)

            # 📲 Send WhatsApp
            send_whatsapp_message(message)

            # 🔥 STORE TASK ID
            last_task_id = task.id

def start_scheduler():
    scheduler.add_job(check_tasks, "interval", seconds=30)
    scheduler.start()