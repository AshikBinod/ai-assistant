from fastapi import FastAPI
from datetime import datetime
from task_manager import create_task, get_tasks, complete_task
from scheduler import start_scheduler
from models import Base
from database import engine
from ai_parser import parse_command
from whatsapp import send_whatsapp_message  # 🔥 NEW

app = FastAPI()

# 🚀 Startup
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    start_scheduler()

# 🏠 Home
@app.get("/")
def home():
    return {"status": "Assistant running"}

# ✅ Manual task (browser)
@app.get("/add_task")
def add_task_api(title: str, time: str):
    scheduled_time = datetime.fromisoformat(time)
    create_task(title, scheduled_time)
    return {"message": "Task added"}

# 📋 Get all tasks
@app.get("/tasks")
def tasks():
    return get_tasks()

# ✅ Mark complete
@app.post("/complete_task")
def done(task_id: int):
    complete_task(task_id)
    return {"message": "Task completed"}

# 🤖 AI task creation
@app.get("/ai_add")
def ai_add(input: str):
    data = parse_command(input)

    create_task(
        data["title"],
        datetime.fromisoformat(data["time"])
    )

    return {
        "message": "Task created via AI",
        "parsed": data
    }

# 🔥 TEST WHATSAPP (IMPORTANT)
@app.get("/test_whatsapp")
def test_whatsapp():
    send_whatsapp_message("🔥 Your AI assistant is working!")
    return {"message": "WhatsApp message sent"}