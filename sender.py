import re
import json
import urllib.parse
import webbrowser
import logging
from typing import Dict, Any, Optional
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, PHONE_LEADS_FILE, DATA_DIR

logger = logging.getLogger("SalesAgent.Sender")

def normalize_iran_phone(phone_raw: Optional[str]) -> Optional[str]:
    """
    استانداردسازی شماره همراه ایران به فرمت 989XXXXXXXXX
    """
    if not phone_raw:
        return None
    # حذف تمام کاراکترهای غیرعددی به جز +
    cleaned = re.sub(r"[^\d+]", "", phone_raw.strip())
    if cleaned.startswith("+98"):
        cleaned = cleaned[1:]
    elif cleaned.startswith("0098"):
        cleaned = cleaned[4:]
    elif cleaned.startswith("09"):
        cleaned = "98" + cleaned[1:]
    elif cleaned.startswith("9") and len(cleaned) == 10:
        cleaned = "98" + cleaned
    return cleaned

def save_to_phone_leads(contact: Dict[str, Any], prepared_message: str):
    """
    ذخیره سرنخ‌هایی که درخواست تماس تلفنی داشتند در لیست تماس‌های استاد
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    leads = []
    if PHONE_LEADS_FILE.exists():
        try:
            with open(PHONE_LEADS_FILE, "r", encoding="utf-8") as f:
                leads = json.load(f)
        except Exception:
            leads = []

    lead_entry = {
        "id": contact.get("id"),
        "name": contact.get("name"),
        "phone": contact.get("phone"),
        "business": contact.get("business"),
        "message": contact.get("message"),
        "created_at": contact.get("created_at"),
        "notes_for_call": prepared_message,
        "status": "pending_call"
    }
    # عدم ثبت تکراری
    if not any(x.get("id") == lead_entry["id"] for x in leads):
        leads.append(lead_entry)
        with open(PHONE_LEADS_FILE, "w", encoding="utf-8") as f:
            json.dump(leads, f, ensure_ascii=False, indent=2)
        logger.info(f"مخاطب {contact.get('name')} به لیست تماس‌های تلفنی استاد اضافه شد.")

async def send_via_telegram(phone: str, text: str) -> bool:
    """
    ارسال پیام مستقیم از طریق حساب تلگرام شخصی با Telethon (در صورت تنظیم API_ID)
    """
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        logger.warning("اطلاعات TELEGRAM_API_ID یا TELEGRAM_API_HASH هنوز در .env تنظیم نشده است.")
        return False

    try:
        from telethon import TelegramClient
        session_file = str(DATA_DIR / "abed_telegram.session")
        client = TelegramClient(session_file, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            logger.info("نیاز به تایید اولیه ورود به حساب تلگرام...")
            return False

        # ارسال پیام به مخاطب
        normalized = "+" + normalize_iran_phone(phone)
        await client.send_message(normalized, text)
        await client.disconnect()
        logger.info(f"پیام تلگرام با موفقیت به {normalized} ارسال شد.")
        return True
    except Exception as e:
        logger.error(f"خطا در ارسال پیام تلگرام: {e}")
        return False

def open_in_whatsapp(phone: str, text: str, auto_open_browser: bool = True) -> str:
    """
    تولید لینک و باز کردن WhatsApp Web همراه با متن آماده برای ارسال فوری
    """
    norm_phone = normalize_iran_phone(phone)
    if not norm_phone:
        logger.error(f"شماره تلفن معتبر نیست: {phone}")
        return ""

    encoded_text = urllib.parse.quote(text)
    wa_url = f"https://web.whatsapp.com/send?phone={norm_phone}&text={encoded_text}"

    if auto_open_browser:
        logger.info(f"در حال باز کردن گفتگوی واتساپ برای شماره {norm_phone} در مرورگر...")
        try:
            webbrowser.open(wa_url)
        except Exception as e:
            logger.warning(f"عدم امکان باز کردن خودکار مرورگر: {e}")

    return wa_url
