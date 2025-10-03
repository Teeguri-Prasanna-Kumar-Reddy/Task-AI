# backend/schemas.py
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class ReminderBase(BaseModel):
    remind_at: datetime
    advance_minutes: int = 0  # trigger X minutes before due

class ReminderCreate(ReminderBase):
    task_id: int

class ReminderOut(ReminderBase):
    id: int
    task_id: int
    notified: bool
    created_at: datetime

    class Config:
        orm_mode = True

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_datetime: Optional[datetime] = None
    priority: Optional[int] = 2
    tags: Optional[str] = ""

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    due_datetime: Optional[datetime]
    status: Optional[str]
    priority: Optional[int]
    tags: Optional[str]

class TaskOut(TaskBase):
    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    reminders: List[ReminderOut] = []

    class Config:
        orm_mode = True

class NoteBase(BaseModel):
    title: Optional[str]
    content: str

class NoteCreate(NoteBase):
    pass

class NoteOut(NoteBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    tags: Optional[str] = ""

    class Config:
        orm_mode = True

# AI endpoints
class AIQuery(BaseModel):
    prompt: str
    context: Optional[str] = None

class AISummaryRequest(BaseModel):
    text: str
    max_length: Optional[int] = 120
