# backend/migrate_notes.py
from backend.database import engine

with engine.connect() as conn:
    conn.execute("ALTER TABLE notes ADD COLUMN tags VARCHAR DEFAULT ''")
    print("✅ 'tags' column added to notes table")
