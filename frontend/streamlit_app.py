# frontend/streamlit_app.py
import streamlit as st
import requests
import os
from datetime import datetime
import time

import pytz
IST = pytz.timezone("Asia/Kolkata")

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="TaskAI - Assistant Manager", layout="wide")

st.title("TaskAI — Daily Task & Notes Manager (Demo)")

# Sidebar: Add task
st.sidebar.header("Create Task / Note")
with st.sidebar.form("add_task", clear_on_submit=True):
    t_title = st.text_input("Title")
    t_description = st.text_area("Description")
    t_due = st.text_input("Due datetime (YYYY-MM-DD HH:MM)")  # simple input
    t_priority = st.selectbox("Priority", [1, 2, 3], index=1)
    t_tags = st.text_input("Tags (comma separated)")
    submitted = st.form_submit_button("Add Task")
    if submitted:
        due_dt = None
        if t_due:
            try:
                due_dt = datetime.strptime(t_due.strip(), "%Y-%m-%d %H:%M").isoformat()
            except Exception:
                st.error("Invalid date format. Use YYYY-MM-DD HH:MM")
        payload = {
            "title": t_title,
            "description": t_description,
            "due_datetime": due_dt,
            "priority": t_priority,
            "tags": t_tags
        }
        resp = requests.post(f"{BACKEND_URL}/tasks", json=payload)
        if resp.status_code == 200:
            task = resp.json()
            st.success("Task added ✅")

            # Highlight newly created task for 10s
            if "highlight_ids" not in st.session_state:
                st.session_state["highlight_ids"] = {}
            st.session_state["highlight_ids"][task["id"]] = time.time()
            st.rerun()


        else:
            st.error(f"Error saving task: {resp.text}")
        

with st.sidebar.form("add_note", clear_on_submit=True):
    n_title = st.text_input("Note title", key="note_title")
    n_content = st.text_area("Content", key="note_content")
    n_sub = st.form_submit_button("Add Note")
    if n_sub:
        resp = requests.post(f"{BACKEND_URL}/notes", json={"title": n_title, "content": n_content})
        if resp.status_code == 200:
            st.success("Note saved")
        else:
            st.error("Error saving note")





# Main area: Tabs
tab1, tab2, tab3 = st.tabs(["Tasks", "Notes", "AI Assistant"])

with tab1:
    st.header("Tasks")
    col1, col2 = st.columns([3, 1])
    with col2:
        flt = st.selectbox("Filter", ["all", "today", "overdue"])
        refresh = st.button("Refresh")

    params = {}
    if flt != "all":
        params["filter"] = flt

    try:
        r = requests.get(f"{BACKEND_URL}/tasks", params=params)
        tasks = r.json()
    except Exception as e:
        st.error("Cannot contact backend. Make sure FastAPI server is running.")
        tasks = []

    if not tasks:
        st.info("No tasks found. Add one from the sidebar!")
    else:
        # 🔹 Prune old highlights (older than 10s)
        # highlight_ids = st.session_state.get("highlight_ids", {})
        # now = time.time()
        # highlight_ids = {tid: ts for tid, ts in highlight_ids.items() if now - ts < 5}
        
        # st.session_state["highlight_ids"] = highlight_ids
        for t in tasks:
            try:
                dt = datetime.fromisoformat(t["due_datetime"])
                # if stored as naive (no tz) assume it's UTC (but we now store UTC)
                if dt.tzinfo is None:
                    dt = IST.localize(dt)
                # Convert to local timezone for display
                local_dt = dt.astimezone(IST)  # no args -> local system timezone
                due_str = local_dt.strftime("%d %b %Y, %I:%M %p")
            except Exception:
                due_str = t["due_datetime"]

            # 👇 Add highlight style if this is the latest voice task
            # highlight = ""
            # if t["id"] in st.session_state.get("highlight_ids", {}):
            #     highlight = "background-color: yellow;"


            with st.container():
                st.markdown(
                    f"""
                    <div style="padding: 12px; margin-bottom:10px; border: 1px solid #ddd;
                                border-radius: 10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <b>{t['title']}</b>  
                                <span style="color:gray;">({t['status']})</span><br>
                                <small>
                            Priority: {t['priority']} | Tags: {t.get('tags','')} | 
                            ⏳ Due: {due_str}
                        </small>
                            </div>
                        </div>
                        {f"<p style='margin-top:8px;'>{t['description']}</p>" if t.get("description") else ""}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # actual Streamlit buttons (logic behind the HTML buttons)
            c1, c2 = st.columns([1, 1], gap="small")
            with c1:
                if st.button("✅ Done", key=f"done_{t['id']}"):
                    payload = {
                        "title": t["title"],
                        "description": t.get("description", ""),
                        "due_datetime": t.get("due_datetime"),
                        "priority": t.get("priority", 2),
                        "tags": t.get("tags", ""),
                        "status": "done",
                    }
                    resp = requests.put(f"{BACKEND_URL}/tasks/{t['id']}", json=payload)
                    if resp.status_code == 200:
                        st.rerun()
                    else:
                        st.error(f"Error: {resp.text}")
            with c2:
                if st.button("🗑 Delete", key=f"del_{t['id']}"):
                    resp = requests.delete(f"{BACKEND_URL}/tasks/{t['id']}")
                    if resp.status_code == 200:
                        st.rerun()
                        

    # Show reminders under tasks
    st.subheader("🔔 Reminders")
    try:
        rem_resp = requests.get(f"{BACKEND_URL}/reminders")
        reminders = rem_resp.json()
    except Exception:
        reminders = []

    if not reminders:
        st.info("No reminders scheduled.")
    else:
        local_tz = datetime.now().astimezone().tzinfo
        for r in reminders:
            try:
                remind_at_str = r["remind_at"]
                remind_at_utc = datetime.fromisoformat(remind_at_str.replace("Z", "+00:00"))
                remind_at_local = remind_at_utc.astimezone(local_tz)

                st.markdown(
                    f"🔔 **Task #{r['task_id']}** → "
                    f"{remind_at_local.strftime('%Y-%m-%d %I:%M %p (%Z)')}"
                )
            except Exception:
                remind_str = r.get("remind_at")

            # st.write(f"⏰ Task #{r['task_id']} — Remind at: {remind_str} — Notified: {r['notified']}")
    
    # # Voice capture HTML (uses Web Speech API). It will POST transcript to BACKEND_URL/tasks
    # st.write("---")
    # st.subheader("Voice input (browser)")
    # st.write("Click 'Start Listening', speak a task like: 'Remind me to call Ravi tomorrow at 6pm'")

    # VOICE_HTML = f"""
    # <div>
    # <button id="startBtn">🎤 Start Voice</button>
    # <button id="stopBtn">🛑 Stop Voice</button>
    # <p id="status" style="color: white;">Idle</p>
    # </div>

    # <script>
    # let recognition = null;

    # if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {{
    # document.getElementById("status").innerText = "SpeechRecognition not supported in this browser.";
    # }} else {{
    # const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    # recognition = new SpeechRecognition();
    # recognition.lang = 'en-US';
    # recognition.interimResults = false;
    # recognition.continuous = false;

    # recognition.onstart = () => document.getElementById("status").innerText = "Listening...";
    # recognition.onend = () => document.getElementById("status").innerText = "Idle";
    # recognition.onerror = (e) => document.getElementById("status").innerText = "Error: " + e.error;
    # recognition.onresult = (event) => {{
    #     const transcript = event.results[0][0].transcript;
    #     console.log("🎤 Heard:", transcript);
    #     document.getElementById("status").innerText = "Heard: " + transcript;

    #     fetch("{BACKEND_URL}/tasks/voice", {{
    #     method: "POST",
    #     headers: {{ "Content-Type": "application/json" }},
    #     body: JSON.stringify({{ text: transcript }})
    #     }}).then(r => r.json()).then(data => {{
    #     document.getElementById("status").innerText = "✅ Task created";

    #     // Save new taskId into sessionStorage
    #     let ids = JSON.parse(sessionStorage.getItem("highlight_ids") || "[]");
    #     ids.push(data.id);
    #     sessionStorage.setItem("highlight_ids", JSON.stringify(ids));

    #     // 🔔 Tell parent Streamlit app to reload
    #     parent.postMessage({{ type: "voice_task_created" }}, "*");
    #     }}).catch(err => {{
    #     document.getElementById("status").innerText = "❌ Error: " + err;
    #     }});
    # }};
    # }}

    # document.getElementById("startBtn").onclick = () => {{ recognition && recognition.start(); }};
    # document.getElementById("stopBtn").onclick = () => {{ recognition && recognition.stop(); }};
    # </script>
    # """
    # st.components.v1.html(VOICE_HTML, height=180)

    # === Voice Input (mobile friendly via Whisper backend) ===
    st.write("---")
    st.subheader("🎤 Voice Input (Whisper)")
    audio_bytes = st.audio_input("Record your voice")

    if audio_bytes is not None:
        st.info("⏳ Transcribing...")
        files = {"file": ("voice.wav", audio_bytes, "audio/wav")}
        try:
            # Call backend /stt for transcription
            stt_resp = requests.post(f"{BACKEND_URL}/stt", files=files, data={"language": "en"})
            if stt_resp.status_code == 200:
                text = stt_resp.json().get("text", "")
                st.success(f"Recognized: {text}")

                # Send to /tasks/voice for task creation
                task_resp = requests.post(f"{BACKEND_URL}/tasks/voice", json={"text": text})
                # print("new task response:",task_resp)
                if task_resp.status_code == 200:
                    new_task = task_resp.json()
                    # print(new_task)
                    st.success(f"✅ Task created: {new_task['title']}")

                    # 🔹 Use dict {task_id: timestamp} instead of list
                    # if "highlight_ids" not in st.session_state:
                    #     st.session_state["highlight_ids"] = {}
                    # st.session_state["highlight_ids"][new_task["id"]] = time.time()

                    # st.rerun()
                else:
                    st.error(f"Task creation failed: {task_resp.text}")
            else:
                st.error(f"STT failed: {stt_resp.text}")
        except Exception as e:
            st.error(f"Error: {e}")


with tab2:
    notes = requests.get(f"{BACKEND_URL}/notes").json()

    st.subheader("Your Notes")
    for n in notes:
        with st.expander(n["title"] or "Untitled"):
            st.write(n["content"])
            st.caption(f"Tags: {n['tags']}")
            st.caption(f"Created at: {n['created_at']}")

            # Delete button
            if st.button("Delete", key=f"del_note_{n['id']}"):
                resp = requests.delete(f"{BACKEND_URL}/notes/{n['id']}")
                if resp.status_code == 200:
                    st.success("Note deleted successfully")
                    st.rerun()
                else:
                    st.error(f"Error: {resp.text}")

with tab3:
    st.header("AI Assistant")
    st.write("Ask natural language questions about your tasks/notes (e.g., 'What is due today?').")
    q = st.text_input("Question", key="ai_question")
    if st.button("Ask AI"):
        payload = {"prompt": q}
        try:
            r = requests.post(f"{BACKEND_URL}/ai/query", json=payload)
            ans = r.json().get("answer", "")
            st.success(ans)
        except Exception as e:
            st.error("AI endpoint error: " + str(e))

    st.write("---")
    st.write("Quick summarizer (paste note text)")
    text = st.text_area("Text to summarize")
    if st.button("Summarize"):
        try:
            r = requests.post(f"{BACKEND_URL}/ai/summarize", json={"text": text})
            st.info(r.json().get("summary", ""))
        except Exception as e:
            st.error("Error: " + str(e))

    # (inside tab3: AI Assistant)

    # st.write("---")
    # st.write("Categorize text (suggest tags for your note)")
    # cat_text = st.text_area("Text to categorize")
    # if st.button("Categorize"):
    #     try:
    #         r = requests.post(f"{BACKEND_URL}/ai/categorize", json={"text": cat_text})
    #         tags = r.json().get("tags", [])
    #         if tags:
    #             st.success("Suggested categories: " + ", ".join(tags))
    #         else:
    #             st.info("No categories found.")
    #     except Exception as e:
    #         st.error("Error: " + str(e))




# from streamlit_js_eval import streamlit_js_eval

# # Reload the app when message is received from VOICE_HTML
# streamlit_js_eval(
#     js_expressions="""
#     window.addEventListener("message", function(event) {
#         if (event.data && event.data.type === "voice_task_created") {
#             parent.window.location.reload();
#         }
#     });
#     """,
#     key="reload_listener"
# )





