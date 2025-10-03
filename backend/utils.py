# backend/utils.py
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

def notify_console(message: str):
    ts = datetime.utcnow().isoformat()
    print(f"[notify] {ts} - {message}")

# Desktop notify (optional)
def notify_desktop(title: str, message: str):
    """
    Use plyer if installed. Otherwise no-op.
    """
    try:
        from plyer import notification
        notification.notify(title=title, message=message, timeout=8)
        print("notified")
    except Exception as e:
        # plyer not installed or unsupported platform
        print(f"some error occured in desktop notification!! {e}")
        pass


# utils.py
import os
import requests

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def notify_telegram(title: str, body: str):
    message = f"📌 *{title}*\n\n{body}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print("Telegram notification failed:", e)


