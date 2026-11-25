import json
import time
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from config import DATA_DIR, LOGS_DIR, HISTORY_FILE, PHONE_LEADS_FILE
from responder import generate_personalized_response
from sender import open_in_whatsapp, send_via_telegram, save_to_phone_leads, normalize_iran_phone

LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "agent.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SalesAgent.Core")

def load_processed_ids() -> set:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("processed_ids", []))
        except Exception:
            return set()
    return set()

def save_processed_id(contact_id: Any):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    current_ids = list(load_processed_ids())
    if contact_id not in current_ids:
        current_ids.append(contact_id)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"processed_ids": current_ids, "last_update": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)

class DailySalesAgent:
    def __init__(self):
        self.local_contacts_file = DATA_DIR / "contacts_تماس_با_ما.json"

    def fetch_unread_contact_us_messages(self) -> List[Dict[str, Any]]:
        """
        واکشی پیام‌های فرم تماس با ما (ابتدا از پنل آنلاین، در صورت عدم دسترسی از دیتابیس محلی)
        """
        try:
            from browser_contact_manager import BrowserContactManager
            manager = BrowserContactManager(headless=True)
            live_contacts = manager.fetch_contact_messages(unread_only=True)
            if live_contacts:
                return live_contacts
        except Exception as e:
            logger.info(f"استفاده از پایگاه داده ذخیره شده پیام‌های تماس با ما: {e}")

        if self.local_contacts_file.exists():
            with open(self.local_contacts_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def process_new_contacts(self, auto_open_whatsapp: bool = False):
        """
        بررسی پیام‌های بخش «تماس با ما» و آماده‌سازی پاسخ بر اساس کانال ترجیحی مشتری
        """
        logger.info("🔍 در حال بررسی پیام‌های فرم «تماس با ما»...")
        contacts = self.fetch_unread_contact_us_messages()

        if not contacts:
            logger.info("✅ هیچ پیام جدیدی در بخش تماس با ما یافت نشد.")
            return []

        processed_ids = load_processed_ids()
        summary_report = []

        for contact in contacts:
            c_id = contact.get("id") or contact.get("phone")
            name = contact.get("name") or "مشتری گرامی"
            phone = contact.get("phone")
            business = contact.get("business") or ""
            msg = contact.get("message") or ""

            if c_id in processed_ids:
                continue

            response_text, channel = generate_personalized_response(contact)
            action_result = ""

            # ۱. اگر مشتری درخواست تماس تلفنی داشته است (تماس توسط خود استاد)
            if channel == "phone":
                save_to_phone_leads(contact, response_text)
                action_result = "📞 ثبت در لیست تماس‌های تلفنی خودتان"

            # ۲. اگر مشتری درخواست تلگرام داشته است
            elif channel == "telegram":
                norm_phone = normalize_iran_phone(phone)
                t_link = f"https://t.me/+{norm_phone}" if norm_phone else "https://t.me/abedahm"
                action_result = f"💬 تلگرام ({t_link})"

            # ۳. اگر مشتری درخواست واتساپ داشته است
            elif channel == "whatsapp":
                wa_url = open_in_whatsapp(phone, response_text, auto_open_browser=auto_open_whatsapp)
                action_result = f"🟢 واتساپ (لینک چت با متن آماده)"

            summary_report.append({
                "id": c_id,
                "name": name,
                "phone": phone,
                "business": business,
                "channel": channel,
                "action": action_result,
                "draft": response_text
            })

            save_processed_id(c_id)

        return summary_report

    def run_daily_scheduler(self, run_time: str = "10:00"):
        """
        بررسی خودکار هر روز راس ساعت مشخص
        """
        import schedule
        logger.info(f"⏰ ایجنت فعال شد. بررسی خودکار هر روز راس ساعت {run_time} انجام خواهد شد...")
        schedule.every().day.at(run_time).do(self.process_new_contacts, auto_open_whatsapp=True)

        self.process_new_contacts(auto_open_whatsapp=False)

        while True:
            schedule.run_pending()
            time.sleep(30)
