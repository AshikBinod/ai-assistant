from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from task_manager import get_tasks, complete_task
from whatsapp import send_whatsapp_message

scheduler = BackgroundScheduler()

def check_tasks():
    tasks = get_tasks()
    now = datetime.now()

    for task in tasks:
        if task.status == "pending" and task.scheduled_time <= now:
            message = f"⏰ Reminder: {task.title}"
            print(message)

            # 📲 Send WhatsApp message
            send_whatsapp_message(message)

            # ✅ Mark task as completed to prevent repeat messages
            complete_task(task.id)

def start_scheduler():
    scheduler.add_job(check_tasks, "interval", seconds=30)
    scheduler.start()