# 🧠 TaskAI — AI-Powered Daily Task & Notes Manager

**TaskAI** is a smart productivity assistant that helps you manage your **tasks, notes, reminders, and daily priorities** — all powered by **FastAPI**, **Streamlit**, and **Gemini AI**.

It lets you:
- 🎤 Create tasks using **voice input**
- ✍️ Manage **notes and reminders**
- 🤖 Chat with an **AI Assistant** to summarize or query tasks
- 📆 Get **intelligent due date parsing**
- 💾 Store everything locally or deploy on the cloud

---

## 🚀 Key Features

| Feature | Description |
|----------|-------------|
| 🗓️ **Task Manager** | Add, view, filter, update, and delete tasks with due dates, priorities, and tags. |
| 📝 **Notes Manager** | Save, view, and delete notes for quick information storage. |
| 🎤 **Voice Task Creation** | Speak your tasks naturally — automatically transcribed and added as structured tasks. |
| 🔔 **Reminders System** | View reminders for tasks directly from the dashboard and reminders will be sent to the telegram 15mins prior to the deadline. |
| 🧠 **AI Assistant** | Ask questions about your tasks or notes (e.g., "What’s due today?"). |
| 🗒️ **Summarizer** | Paste text and get a short AI-generated summary. |

---

## 🏗️ Tech Stack

| Layer | Technology |
|--------|-------------|
| **Frontend** | Streamlit |
| **Backend** | FastAPI |
| **AI Model** | Google Gemini (Text + Summarization) |
| **Database** | SQLite |
| **ORM** | SQLAlchemy |
| **Speech-to-Text (STT)** | Whisper / SpeechRecognition |
| **Timezone Handling** | pytz |

---

## 📁 Folder Structure

<img width="301" height="375" alt="image" src="https://github.com/user-attachments/assets/44391d88-644d-4d3f-a306-7855977f5197" />



---

## ⚙️ Setup Instructions

### 🔹 Step 1: Clone the Repository

git clone https://github.com/<your-username>/TaskAI.git
cd TaskAI

### 🔹 Step 2: Start Backend (FastAPI)

cd backend
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

Create a .env file:

GEMINI_API_KEY=your_gemini_key_here
DATABASE_URL=sqlite:///./taskai.db


### 🔹 Step 3: Start Frontend (Streamlit)

cd ../frontend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

Run the Streamlit app:

streamlit run streamlit_app.py

App URL: 👉 http://localhost:8501


## 🧠 Application Workflow

### 🗓️ 1. Manage Tasks

Add manually (via sidebar form)

Add by voice (🎤 record and auto-create)

Mark tasks as Done or Delete

Filter by:

All tasks

Today’s tasks

Overdue tasks

### 📝 2. Manage Notes

Add new notes (title + content)

View and expand notes

Delete notes from dashboard

### 🔔 3. View Reminders

See scheduled reminders per task

All times are localized to Asia/Kolkata (IST)

### 🎤 4. Voice Task Creation

Record voice directly in browser

App sends audio to backend /stt

Gemini AI parses recognized text → creates task automatically

Example:

“Remind me to send project report to sairam tomorrow at 9 AM”
Creates task:

{
  "title": "Send project report to sairam",
  "due_datetime": "2025-10-05T09:00:00+05:30",
  "priority": 2,
  "tags": "voice"
}

### 🤖 5. AI Assistant

Ask: “What are my overdue tasks?”

Ask: “Summarize my last note.”

Use /ai/query for Q&A and /ai/summarize for summarization

## 🧰 Backend API Endpoints
Method	Endpoint	Description
GET	/tasks	List tasks (filter: today, overdue)
POST	/tasks	Add new task
PUT	/tasks/{id}	Update task
DELETE	/tasks/{id}	Delete task
GET	/reminders	Fetch reminders
POST	/notes	Add note
GET	/notes	Get all notes
DELETE	/notes/{id}	Delete note
POST	/tasks/voice	Create task from text
POST	/stt	Speech-to-text endpoint
POST	/ai/query	Ask AI questions about tasks/notes
POST	/ai/summarize	Summarize text

## ☁️ Deployment Guide
Option 1 — Google Cloud Run (Recommended ✅)

Enable Cloud Run API

Build and push Docker image:

gcloud builds submit --tag gcr.io/<project-id>/taskai


Deploy:

gcloud run deploy taskai --image gcr.io/<project-id>/taskai \
--platform managed --region us-central1 --allow-unauthenticated --memory 512Mi

Option 2 — Render Deployment

Render Settings:

Root Directory: backend

Start Command:

uvicorn app:app --host 0.0.0.0 --port 10000 --workers 1


Python Version: 3.10.14

Environment Variables:

GEMINI_API_KEY=your_key
DATABASE_URL=sqlite:///./taskai.db

🔐 Environment Variables
Key	Description
GEMINI_API_KEY	Google Gemini AI API key
DATABASE_URL	SQLite or Postgres URL
BACKEND_URL	Backend endpoint for Streamlit (default: localhost:8000)

🧩 Example Interaction

You say:

“Remind me to call Mom at 6 PM today.”

App responds:
✅ Task created: Call Mom
⏰ Due: 04 Oct 2025, 06:00 PM
📋 Priority: 2
🏷️ Tag: voice

## 🎯 Future Enhancements

🔊 Real-time speech transcription

📱 Mobile-friendly PWA

🔔 Notification reminders via email / Telegram

📊 AI insights dashboard

🗂️ Task categorization by topic




## 🧑‍💻 Author

Teeguri Prasanna Kumar Reddy
💼 AI Engineer | Backend Developer
📧 prasanna20131a4258@gmail.com

🌐 LinkedIn
www.linkedin.com/in/teeguri-prasanna-kumar-reddy
