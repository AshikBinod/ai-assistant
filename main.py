from fastapi import FastAPI
from datetime import datetime
from task_manager import create_task, get_tasks, complete_task
from scheduler import start_scheduler
from models import Base
from database import engine

app = FastAPI()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    start_scheduler()

@app.get("/")
def home():
    return {"status": "Assistant running"}

# ✅ THIS WAS MISSING
@app.get("/add_task")
def add_task_api(title: str, time: str):
    scheduled_time = datetime.fromisoformat(time)
    create_task(title, scheduled_time)
    return {"message": "Task added"}

@app.get("/tasks")
def tasks():
    return get_tasks()

@app.post("/complete_task")
def done(task_id: int):
    complete_task(task_id)
    return {"message": "Task completed"}