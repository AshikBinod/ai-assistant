from fastapi import FastAPI, Request
from fastapi.responses import Response
from datetime import datetime
from task_manager import create_task, get_tasks, complete_task
import scheduler  # 🔥 FIX: import module, NOT variable
from models import Base
from database import engine
from ai_parser import parse_command
from whatsapp import send_whatsapp_message
from twilio.twiml.messaging_response import MessagingResponse

app = FastAPI()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    scheduler.start_scheduler()

@app.get("/")
def home():
    return {"status": "Assistant running"}

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

@app.get("/test_whatsapp")
def test_whatsapp():
    send_whatsapp_message("🔥 Your AI assistant is working!")
    return {"message": "WhatsApp message sent"}

# 🔥 FINAL SMART WEBHOOK
@app.post("/whatsapp_webhook")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    incoming_msg = form.get("Body", "").lower()

    print("Incoming message:", incoming_msg)
    print("Last task ID:", scheduler.last_task_id)  # 🔍 DEBUG

    twilio_response = MessagingResponse()

    if "done" in incoming_msg:
        if scheduler.last_task_id:
            complete_task(scheduler.last_task_id)

            # 🔥 RESET after completion
            scheduler.last_task_id = None

            reply = "✅ Task marked as completed. Good job!"
        else:
            reply = "⚠️ No active task found."

    elif "not yet" in incoming_msg:
        reply = "⏳ Okay, I’ll remind you again soon."

    else:
        reply = "🤖 Reply 'done' when finished or 'not yet'."

    twilio_response.message(reply)

    return Response(
        content=str(twilio_response),
        media_type="application/xml"
    )