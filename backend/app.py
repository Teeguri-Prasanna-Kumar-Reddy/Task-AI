# backend/app.py
from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timezone, timedelta

import backend.models as models
import backend.schemas as schemas
import backend.crud as crud
from backend.database import SessionLocal, engine, Base
from sqlalchemy.orm import Session
import pytz

IST = pytz.timezone("Asia/Kolkata")


# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# app = FastAPI(title="TaskAI - Daily Task & Notes Manager (backend)")

# CORS - allow all for development. Narrow this for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from . import models

@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




@app.post("/tasks", response_model=schemas.TaskOut)
def api_create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    db_task = crud.create_task(db, task)

    # Auto-create a reminder at the task's due_datetime (if present)
    try:
        # Automatically create reminder for due_datetime
        if db_task.due_datetime:

            advance = timedelta(minutes=15)


            remind_at = db_task.due_datetime - advance
            if remind_at.tzinfo is None:  # assume local time if naive
                remind_at = IST.localize(remind_at)

            
            # print(f"remind_at in api_create_task {remind_at}")
            # Convert to UTC before saving
            # remind_at_utc = remind_at.astimezone(pytz.utc)
            # print(f"remind_at_utc in api_create_task {remind_at_utc}")

            rem_schema = schemas.ReminderCreate(
                task_id=db_task.id,
                remind_at=remind_at,
                advance_minutes=15
            )
            crud.create_reminder(db, rem_schema)
    except Exception as e:
        # don't fail task creation if reminder creation fails; log for debug
        print("Warning: failed to auto-create reminder:", e)

    return db_task

@app.get("/tasks", response_model=List[schemas.TaskOut])
def api_list_tasks(filter_by: Optional[str] = Query(None, alias="filter"), db: Session = Depends(get_db)):
    return crud.list_tasks(db, filter_by=filter_by)

@app.get("/tasks/{task_id}", response_model=schemas.TaskOut)
def api_get_task(task_id: int, db: Session = Depends(get_db)):
    t = crud.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return t

@app.put("/tasks/{task_id}", response_model=schemas.TaskOut)
def api_update_task(task_id: int, changes: schemas.TaskUpdate, db: Session = Depends(get_db)):
    t = crud.update_task(db, task_id, changes)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return t

@app.delete("/tasks/{task_id}")
def api_delete_task(task_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_task(db, task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}

# Notes
@app.post("/notes", response_model=schemas.NoteOut)
def api_create_note(note: schemas.NoteCreate, db: Session = Depends(get_db)):
    return crud.create_note(db, note)

@app.get("/notes", response_model=List[schemas.NoteOut])
def api_list_notes(db: Session = Depends(get_db)):
    return crud.list_notes(db)

@app.delete("/notes/{note_id}")
def api_delete_note(note_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_note(db, note_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted successfully"}


# Reminders
@app.post("/reminders", response_model=schemas.ReminderOut)
def api_create_reminder(rem: schemas.ReminderCreate, db: Session = Depends(get_db)):
    # Validate task exists
    t = crud.get_task(db, rem.task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found for reminder")
    return crud.create_reminder(db, rem)

@app.get("/reminders", response_model=List[schemas.ReminderOut])
def api_list_reminders(db: Session = Depends(get_db)):
    # return db.query(models.Reminder).all()
    now = datetime.now(timezone.utc)
    return db.query(models.Reminder).filter(models.Reminder.notified == False).all()



from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from backend import ai, crud, database, schemas
from backend.ai import GeminiWrapper 

# app = FastAPI()

# Create a single Ollama AI instance
# ai_wrapper = ai.AIWrapper(model="llama3", host="http://localhost:11434")
ai_wrapper = GeminiWrapper(model="gemini-2.0-flash")

@app.post("/ai/query")
def ai_query(payload: schemas.AIQuery, db: Session = Depends(get_db)):
    context = payload.context
    if not context:
        # Auto-inject tasks and notes
        tasks = crud.list_tasks(db)
        notes = crud.list_notes(db)
        context_parts = []
        for t in tasks:
            context_parts.append(f"- Task: {t.title} | Status: {t.status} | Due: {t.due_datetime}")
        for n in notes:
            context_parts.append(f"- Note: {n.title} | {n.content[:100]}...")
        context = "\n".join(context_parts) if context_parts else "No tasks or notes available."

    return {"answer": ai_wrapper.query(prompt=payload.prompt, context=context)}

@app.post("/ai/summarize")
def ai_summarize(payload: schemas.AISummaryRequest):
    return {"summary": ai_wrapper.summarize(payload.text, max_length=payload.max_length)}

@app.post("/ai/categorize")
def ai_categorize(payload: schemas.AISummaryRequest):
    return {"categories": ai_wrapper.categorize(payload.text)}



from fastapi import Body, HTTPException, Depends
from sqlalchemy.orm import Session
from dateparser import parse as dateparse
from datetime import datetime
import pytz, json
import google.generativeai as genai
import os


IST = pytz.timezone("Asia/Kolkata")


import json

def extract_task_from_gemini(resp):
    """Extract clean JSON dict from Gemini response safely"""
    raw_text = ""

    # 1. Extract from candidates
    if hasattr(resp, "candidates") and resp.candidates:
        parts = resp.candidates[0].content.parts
        raw_text = "".join(
            p.text for p in parts if hasattr(p, "text")
        ).strip()

    # 2. Remove code fences like ```json ... ```
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```", 2)[1]  # keep inside
        # Sometimes it’s like ```json\n{...}\n``` → so strip `json\n`
        raw_text = raw_text.lstrip("json").strip()

    # 3. Parse JSON
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        print("⚠️ Failed to parse Gemini JSON:", raw_text)
        return {}


gemini = GeminiWrapper(model="gemini-2.0-flash")

@app.post("/tasks/voice")
def api_create_task_voice(payload: dict = Body(...), db: Session = Depends(get_db)):
    """
    Accepts natural language like 'remind me to call Ravi tomorrow at 6pm'
    Uses Gemini to extract structured task details (title, description, due_datetime, priority, tags).
    Fallback to dateparser if needed.
    """
    text = payload.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    task_details = None
    due_dt = None

    # --- Step 1: Try Gemini structured extraction ---
    try:
        prompt = f"""
        You are a task manager assistant.
        The user said: "{text}"

        Respond ONLY in valid JSON. No explanations.

        Format:
        {{
          "title": "short clear task title (remove phrases like 'remind me to')",
          "description": "optional details, default 'Created via voice'",
          "due_datetime": "YYYY-MM-DDTHH:MM (24hr IST). If no due date, return null",
          "priority": 1 (high), 2 (medium), or 3 (low). Default = 2,
          "tags": "voice"
        }}

        Rules:
        - Always output valid JSON, nothing else.
        - If no due date mentioned, set due_datetime = null.
        - Title must be short and clear.
        """

        resp = gemini.query(prompt)
        parsed = extract_task_from_gemini(resp)
        # print(parsed)

        

        task_details = {
            "title": parsed.get("title") or text,
            "description": parsed.get("description") or "Created via voice",
            "due_datetime": parsed.get("due_datetime"),
            "priority": parsed.get("priority", 2),
            "tags": parsed.get("tags") or "voice"
        }

        if task_details["due_datetime"]:
            dt = datetime.strptime(task_details["due_datetime"], "%Y-%m-%dT%H:%M")
            due_dt = IST.localize(dt)
            task_details["due_datetime"] = due_dt.isoformat()

    except Exception as e:
        print("⚠️ Gemini parsing failed:", e)

    # --- Step 2: Fallback to dateparser ---
    if not task_details or not task_details.get("due_datetime"):
        due_dt = dateparse(text, settings={"TIMEZONE": "Asia/Kolkata", "RETURN_AS_TIMEZONE_AWARE": True})
        task_details = {
            "title": text,
            "description": "Created via voice",
            "due_datetime": due_dt.isoformat() if due_dt else None,
            "priority": 2,
            "tags": "voice"
        }

    # --- Step 3: Save Task ---
    task_data = schemas.TaskCreate(**task_details)
    db_task = crud.create_task(db, task_data)

    # --- Step 4: Auto-create reminder ---
    if db_task.due_datetime:
        remind_at = db_task.due_datetime
        if remind_at.tzinfo is None:
            remind_at = IST.localize(remind_at)
        rem_schema = schemas.ReminderCreate(task_id=db_task.id, remind_at=remind_at)
        crud.create_reminder(db, rem_schema)

    print("task_data in api_create_task", task_data)
    print(type(task_data))

    return task_data

from faster_whisper import WhisperModel
import tempfile

# Load model once
model = WhisperModel("small", device="cpu", compute_type="int8")

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Transcribe audio
        segments, _ = model.transcribe(tmp_path)
        text = " ".join([segment.text for segment in segments])

        return {"text": text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# at bottom of backend/app.py (after ai wrapper creation)
from backend.scheduler import start_scheduler_if_needed
start_scheduler_if_needed()
