# backend/crud.py
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

import pytz
IST = pytz.timezone("Asia/Kolkata")

import backend.models as models
import backend.schemas as schemas


import backend.models as models
import backend.ai as ai_wrapper  # import AI wrapper

# TASKS
def create_task(db: Session, task: schemas.TaskCreate) -> models.Task:
    db_task = models.Task(
        title=task.title,
        description=task.description,
        due_datetime=task.due_datetime,
        priority=task.priority or 2,
        tags=task.tags or ""
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_task(db: Session, task_id: int) -> Optional[models.Task]:
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def list_tasks(db: Session, filter_by: Optional[str] = None) -> List[models.Task]:
    q = db.query(models.Task)
    # return q
    if filter_by == "today":
        start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(hour=23, minute=59, second=59)
        q = q.filter(models.Task.due_datetime >= start, models.Task.due_datetime <= end)
    elif filter_by == "overdue":
        q = q.filter(models.Task.due_datetime != None, models.Task.due_datetime < datetime.utcnow(), models.Task.status != "done")
    return q.order_by(models.Task.priority.asc(), models.Task.due_datetime.asc()).all()

def update_task(db: Session, task_id: int, changes: schemas.TaskUpdate) -> Optional[models.Task]:
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    for field, value in changes.dict(exclude_unset=True).items():
        setattr(db_task, field, value)
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int) -> bool:
    db_task = get_task(db, task_id)
    if not db_task:
        return False
    db.delete(db_task)
    db.commit()
    return True

# NOTES
def create_note(db: Session, note: schemas.NoteCreate) -> models.Note:
    # Call AI categorizer
    tags_list = ai_wrapper.categorize(note.content)
    tags_str = ", ".join(tags_list)
    db_note = models.Note(title=note.title, content=note.content, tags=tags_str)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

def list_notes(db: Session) -> List[models.Note]:
    return db.query(models.Note).order_by(models.Note.created_at.desc()).all()

def delete_note(db: Session, note_id: int) -> bool:
    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not note:
        return False
    db.delete(note)
    db.commit()
    return True


# REMINDERS
def create_reminder(db: Session, rem: schemas.ReminderCreate) -> models.Reminder:
    """
    Ensure remind_at is stored as timezone-aware UTC.
    Accepts rem.remind_at possibly naive or aware.
    """
    remind_at = rem.remind_at
    # If naive datetime, assume IST
    if remind_at.tzinfo is None:
        remind_at = IST.localize(remind_at)
    else:
        # Convert to IST if it has another timezone
        remind_at = remind_at.astimezone(IST)


    db_rem = models.Reminder(task_id=rem.task_id, remind_at=remind_at)
    db.add(db_rem)
    db.commit()
    db.refresh(db_rem)
    return db_rem

def get_due_reminders(db: Session, now: datetime) -> List[models.Reminder]:
    return db.query(models.Reminder).filter(models.Reminder.remind_at <= now, models.Reminder.notified == False).all()

def mark_reminder_notified(db: Session, reminder_id: int):
    r = db.query(models.Reminder).filter(models.Reminder.id == reminder_id).first()
    if r:
        r.notified = True
        db.commit()
        db.refresh(r)

def delete_reminder(db: Session, reminder_id: int):
    rem = db.query(models.Reminder).filter(models.Reminder.id == reminder_id).first()
    if rem:
        db.delete(rem)
        db.commit()
        return True
    return False
