# backend/scheduler.py
import threading
import time
from datetime import datetime, timezone
from typing import Optional
import os

from backend.database import SessionLocal
import backend.crud as crud
import backend.utils as utils

import pytz

CHECK_INTERVAL_SECONDS = int(os.getenv("SCHED_CHECK_INTERVAL", "30"))  # frequency to poll reminders
IST = pytz.timezone("Asia/Kolkata")

class ReminderWorker(threading.Thread):
    def __init__(self, interval_seconds: int = CHECK_INTERVAL_SECONDS):
        super().__init__(daemon=True)
        self.interval = interval_seconds
        self._stop = threading.Event()

    def run(self):
        print(f"[scheduler] Starting ReminderWorker (interval={self.interval}s)")

        while not self._stop.is_set():
            try:
                now = datetime.now(IST)
                print("[scheduler] checking at:", now)
                db = SessionLocal()
                due = crud.get_due_reminders(db, now)
                # print("[scheduler] due reminders:", len(due))
                for r in due:
                    # fetch task for display
                    task = crud.get_task(db, r.task_id)
                    title = task.title if task else f"Task #{r.task_id}"

                    # Calculate actual trigger time
                    trigger_time = r.remind_at
                    if trigger_time.tzinfo is None:
                        trigger_time = IST.localize(trigger_time)  # make aware
                    if hasattr(r, "advance_minutes") and r.advance_minutes:
                        from datetime import timedelta
                        trigger_time = r.remind_at - timedelta(minutes=r.advance_minutes)


                    now = datetime.now(IST)
                    print(f"now : {now}")
                    print(f"trigger time : {trigger_time}")
                    if now >= trigger_time:
                        body = f"Reminder for task: {title} at {r.remind_at.strftime('%Y-%m-%d %I:%M %p')}"
                        print("console notifier")
                        utils.notify_console(body)
                        utils.notify_telegram(title, body) 
                        crud.mark_reminder_notified(db, r.id)
                        crud.delete_reminder(db, r.id)
                    
                db.close()
            except Exception as e:
                print(f"[scheduler] error: {e}")
            # sleep
            self._stop.wait(self.interval)

    def stop(self):
        self._stop.set()

# start worker automatically if module imported in the main process
_worker: Optional[ReminderWorker] = None

def start_scheduler_if_needed():
    global _worker
    if _worker is None:
        _worker = ReminderWorker()
        _worker.start()

# You can call start_scheduler_if_needed() from your app startup

