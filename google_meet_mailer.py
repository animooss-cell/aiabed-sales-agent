"""
Google Meet & Gmail Invitation Dispatcher for Abdullah Ahmadian (aiabed.ir)
Sends professional Google Meet invitation emails from aiabed.ir2026@gmail.com.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime
import json
import logging
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MEETINGS_FILE = DATA_DIR / "scheduled_meetings.json"
logger = logging.getLogger("MeetMailer")

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

GMAIL_SENDER = os.environ.get("GMAIL_SENDER", "aiabed.ir2026@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

def generate_meet_html(customer_name: str, meeting_time: str, meet_link: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            background-color: #f7f9fc;
            margin: 0;
            padding: 20px;
            color: #333333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            border: 1px solid #e1e8ed;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #ffffff;
            padding: 25px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 22px;
            font-weight: 700;
        }}
        .content {{
            padding: 30px;
            line-height: 1.8;
            font-size: 15px;
        }}
        .meeting-box {{
            background-color: #f0f7ff;
            border-right: 4px solid #2a5298;
            border-radius: 8px;
            padding: 18px 20px;
            margin: 20px 0;
        }}
        .meeting-box p {{
            margin: 6px 0;
            font-weight: 600;
        }}
        .btn {{
            display: inline-block;
            background-color: #0084ff;
            color: #ffffff !important;
            text-decoration: none;
            padding: 12px 28px;
            border-radius: 8px;
            font-weight: 700;
            margin: 20px 0;
            text-align: center;
        }}
        .footer {{
            background-color: #f8fafc;
            border-top: 1px solid #eef2f6;
            padding: 20px 30px;
            font-size: 13px;
            color: #64748b;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>جلسه آنلاین مشاوره و ارزیابی هوش مصنوعی</h1>
            <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px;">مهندس عبدالله احمدیان | aiabed.ir</p>
        </div>
        <div class="content">
            <p>سلام <strong>{customer_name}</strong> عزیز، وقتتون بخیر 🙏</p>
            <p>خوشحالم که برای یادگیری و استقرار کاربردی هوش مصنوعی در مسیر کاری‌تون مصمم هستید. همان‌طور که در گفتگوی تلگرام هماهنگ کردیم، جلسه آنلاین ما در بستر <strong>Google Meet</strong> آماده‌سازی شد:</p>
            
            <div class="meeting-box">
                <p>📅 <strong>زمان جلسه:</strong> {meeting_time}</p>
                <p>📍 <strong>محل برگزاری:</strong> بستر امن Google Meet</p>
                <p>🎯 <strong>محور جلسه:</strong> ارائه نقشه راه اختصاصی هوش مصنوعی، تکنیک‌های سناریونویسی و اتوماسیون</p>
            </div>

            <div style="text-align: center;">
                <a href="{meet_link}" class="btn" target="_blank">ورود به جلسه Google Meet</a>
            </div>

            <p style="font-size: 13px; color: #666;">اگر دکمه بالا کار نکرد، می‌توانید از لینک مستقیم زیر استفاده فرمایید:<br>
            <a href="{meet_link}" style="color: #0084ff; word-break: break-all;">{meet_link}</a></p>

            <p>پیشنهاد می‌کنم چند دقیقه قبل از شروع جلسه، اینترنت و مرورگر خود را بررسی فرمایید. در صورت هرگونه سوال یا تغییر زمان، از طریق تلگرام یا شماره مستقیم در خدمت شما هستم.</p>
        </div>
        <div class="footer">
            <p style="margin: 0 0 6px 0;"><strong>عبدالله احمدیان</strong></p>
            <p style="margin: 0;">مشاور و مدرس ارشد هوش مصنوعی سازمانی و کسب‌وکار در اهواز<br>
            شماره تماس: ۰۹۱۶۱۰۰۲۵۵۰ | وب‌سایت: <a href="https://aiabed.ir" style="color: #2a5298;">aiabed.ir</a></p>
        </div>
    </div>
</body>
</html>
"""

def schedule_and_send_meet_invite(customer_name: str, customer_email: str, meeting_time: str = "یکشنبه ۹ آذر ساعت ۱۷:۰۰", meet_link: str = "https://meet.google.com/abed-ai-session") -> bool:
    """
    Saves meeting record and sends official invitation email from aiabed.ir2026@gmail.com
    """
    DATA_DIR.mkdir(exist_ok=True)
    
    # Save to local record
    meetings = []
    if MEETINGS_FILE.exists():
        try:
            with open(MEETINGS_FILE, "r", encoding="utf-8") as f:
                meetings = json.load(f)
        except Exception:
            pass

    record = {
        "customer_name": customer_name,
        "customer_email": customer_email,
        "meeting_time": meeting_time,
        "meet_link": meet_link,
        "created_at": datetime.now().isoformat(),
        "sent_status": False
    }

    if not GMAIL_APP_PASSWORD:
        logger.warning("GMAIL_APP_PASSWORD not set in environment. Saved meeting to queue without SMTP dispatch.")
        record["note"] = "Waiting for GMAIL_APP_PASSWORD"
        meetings.append(record)
        with open(MEETINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(meetings, f, ensure_ascii=False, indent=2)
        return False

    # Dispatch via Cloud GitHub Actions API if GITHUB_TOKEN is available, else use direct SMTP
    github_token = os.environ.get("GITHUB_TOKEN", "")
    if github_token:
        try:
            import requests
            api_url = "https://api.github.com/repos/animooss-cell/aiabed-sales-agent/actions/workflows/instant_meet_email.yml/dispatches"
            headers = {
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "SalesAgent"
            }
            payload = {
                "ref": "main",
                "inputs": {
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "meeting_time": meeting_time,
                    "meet_link": meet_link
                }
            }
            res = requests.post(api_url, json=payload, headers=headers, timeout=10)
            if res.status_code in [200, 204]:
                logger.info(f"🚀 INSTANT Google Meet email dispatched via Cloud Relay to {customer_email}!")
                record["sent_status"] = True
                meetings.append(record)
                with open(MEETINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(meetings, f, ensure_ascii=False, indent=2)
                return True
            else:
                logger.warning(f"Cloud dispatch status {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Error calling Cloud Relay: {e}")

    # Fallback to direct SMTP
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"دعوت‌نامه جلسه آنلاین Google Meet | مهندس عبدالله احمدیان ({customer_name})"
        msg["From"] = f"عبدالله احمدیان <{GMAIL_SENDER}>"
        msg["To"] = customer_email

        html_content = generate_meet_html(customer_name, meeting_time, meet_link)
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=5) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, [customer_email], msg.as_string())

        record["sent_status"] = True
        meetings.append(record)
        with open(MEETINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(meetings, f, ensure_ascii=False, indent=2)

        logger.info(f"Successfully sent Google Meet invitation to {customer_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {customer_email}: {e}")
        record["error"] = str(e)
        meetings.append(record)
        with open(MEETINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(meetings, f, ensure_ascii=False, indent=2)
        return False

if __name__ == "__main__":
    test_result = schedule_and_send_meet_invite(
        customer_name="رقیه خانم",
        customer_email="example@gmail.com",
        meeting_time="یکشنبه ۹ آذر ساعت ۱۷:۰۰",
        meet_link="https://meet.google.com/abed-ai-session"
    )
    print("Execution complete. Saved to scheduled_meetings.json")
