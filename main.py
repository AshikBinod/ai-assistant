from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from datetime import datetime
from twilio.twiml.messaging_response import MessagingResponse
import logging

from models import Base
from database import engine
from task_manager import (
    create_task, get_tasks, complete_task, snooze_task,
    get_active_task_id, clear_active_task
)
from ai_parser import parse_command
from whatsapp import send_whatsapp_message
import scheduler as sched

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── STARTUP / SHUTDOWN ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    sched.start_scheduler()
    logger.info("✅ AI Assistant started")
    yield
    # Shutdown
    sched.stop_scheduler()
    logger.info("🛑 AI Assistant stopped")


app = FastAPI(title="AI Assistant", lifespan=lifespan)


# ─── REQUEST MODELS ───────────────────────────────────────────────────────────

class AddTaskRequest(BaseModel):
    title: str
    time: str  # ISO 8601 format


class AIAddRequest(BaseModel):
    input: str


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"status": "AI Assistant is running 🚀"}


@app.get("/tasks")
def list_tasks(status: str = None):
    """List all tasks. Optional ?status=pending|completed|snoozed"""
    return get_tasks(status=status)


@app.post("/add_task")
def add_task_api(body: AddTaskRequest):
    """Manually add a task with a specific time."""
    try:
        scheduled_time = datetime.fromisoformat(body.time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use ISO 8601.")
    task = create_task(body.title, scheduled_time)
    return {"message": "Task added", "task": task}


@app.post("/ai_add")
def ai_add(body: AIAddRequest):
    """Create a task using natural language (AI-parsed)."""
    if not body.input.strip():
        raise HTTPException(status_code=400, detail="Input cannot be empty")

    data = parse_command(body.input)
    task = create_task(data["title"], datetime.fromisoformat(data["time"]))
    return {"message": "Task created via AI", "task": task}


@app.post("/complete_task")
def mark_done(task_id: int):
    success = complete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task #{task_id} not found")
    return {"message": f"Task #{task_id} completed"}


@app.get("/test_whatsapp")
def test_whatsapp():
    sent = send_whatsapp_message("🔥 Your AI assistant is live and working!")
    if sent:
        return {"message": "WhatsApp message sent"}
    raise HTTPException(status_code=500, detail="Failed to send WhatsApp message")


# ─── WHATSAPP WEBHOOK ────────────────────────────────────────────────────────

@app.post("/whatsapp_webhook")
async def whatsapp_webhook(request: Request):
    """
    Handle incoming WhatsApp messages from Twilio.

    Supported commands:
      done        → complete active task
      snooze      → delay active task by 10 minutes
      add <task>  → create a new task via AI
      help        → show available commands
    """
    form = await request.form()
    incoming_msg = form.get("Body", "").strip()
    sender = form.get("From", "")

    logger.info(f"[Webhook] From: {sender} | Message: '{incoming_msg}'")

    twiml = MessagingResponse()
    msg_lower = incoming_msg.lower()

    # ── DONE ──────────────────────────────────────────────────────────────────
    if msg_lower in ("done", "✅", "completed", "finish", "finished"):
        active_id = get_active_task_id()
        if active_id:
            complete_task(active_id)
            clear_active_task()
            reply = "✅ Great job! Task marked as completed."
        else:
            reply = "⚠️ No active task found. Use 'add <task>' to create one."

    # ── SNOOZE ────────────────────────────────────────────────────────────────
    elif msg_lower in ("snooze", "later", "not yet", "remind me later"):
        active_id = get_active_task_id()
        if active_id:
            snooze_task(active_id, minutes=10)
            clear_active_task()
            reply = "⏳ Got it. I'll remind you again in 10 minutes."
        else:
            reply = "⚠️ No active task to snooze."

    # ── ADD TASK VIA WHATSAPP ─────────────────────────────────────────────────
    elif msg_lower.startswith("add "):
        user_input = incoming_msg[4:].strip()
        if user_input:
            data = parse_command(user_input)
            task = create_task(data["title"], datetime.fromisoformat(data["time"]))
            reply = (
                f"✅ Task added!\n"
                f"📌 *{task['title']}*\n"
                f"⏰ Scheduled: {task['scheduled_time']}"
            )
        else:
            reply = "⚠️ Please provide a task. Example: add remind me to drink water in 30 minutes"

    # ── LIST TASKS ────────────────────────────────────────────────────────────
    elif msg_lower in ("tasks", "list", "show tasks"):
        pending = get_tasks(status="pending")
        if pending:
            task_list = "\n".join([f"• {t['title']} @ {t['scheduled_time']}" for t in pending[:5]])
            reply = f"📋 Pending tasks:\n{task_list}"
        else:
            reply = "✨ No pending tasks! Use 'add <task>' to create one."

    # ── HELP ─────────────────────────────────────────────────────────────────
    elif msg_lower in ("help", "?", "hi", "hello"):
        reply = (
            "🤖 *AI Assistant Commands:*\n\n"
            "• *done* — complete the current reminder\n"
            "• *snooze* — remind me again in 10 min\n"
            "• *add <task>* — create a new task\n"
            "  e.g. add call mom in 2 hours\n"
            "• *tasks* — list pending tasks\n"
            "• *help* — show this menu"
        )

    # ── UNKNOWN ───────────────────────────────────────────────────────────────
    else:
        reply = (
            "🤖 I didn't understand that.\n"
            "Reply *help* to see available commands."
        )

    twiml.message(reply)
    return Response(content=str(twiml), media_type="application/xml")
