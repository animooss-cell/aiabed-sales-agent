import os
import json
import logging
import urllib.parse
from datetime import datetime
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright

from responder import generate_personalized_response
from sender import normalize_iran_phone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("GitHubAction.SalesAgent")

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = DATA_DIR / "processed_contacts.json"
PHONE_LEADS_FILE = DATA_DIR / "phone_calls_todo.json"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OWNER_ID = os.getenv("TELEGRAM_OWNER_ID", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

def load_processed_ids() -> set:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("processed_ids", []))
        except Exception:
            return set()
    return set()

def save_processed_id(contact_id: str):
    ids = list(load_processed_ids())
    if contact_id not in ids:
        ids.append(contact_id)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"processed_ids": ids, "last_updated": datetime.utcnow().isoformat()}, f, ensure_ascii=False, indent=2)

def notify_owner_via_telegram(title: str, text: str, buttons: list = None):
    """
    ارسال گزارش یا نوتیفیکیشن فوری به تلگرام صاحب وب‌سایت
    """
    if not OWNER_ID:
        logger.info("TELEGRAM_OWNER_ID تنظیم نشده است.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": OWNER_ID,
        "text": f"🔔 *{title}*\n\n{text}",
        "parse_mode": "Markdown"
    }
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}

    try:
        with httpx.Client(timeout=15.0) as client:
            client.post(url, json=payload)
    except Exception as e:
        logger.error(f"خطا در ارسال نوتیفیکیشن تلگرام: {e}")

def run_github_agent():
    logger.info("🚀 اجرای بررسی دوره‌ای پیام‌های تماس با ما در سرورهای ابری گیت‌هاب...")
    processed_ids = load_processed_ids()
    new_contacts = []

    # واکشی پیام‌ها از سایت با Playwright
    if ADMIN_EMAIL and ADMIN_PASSWORD:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # ورود به پنل
                page.goto("https://aiabed.ir/admin/login", wait_until="networkidle", timeout=30000)
                page.fill('input[type="email"], input[name="email"]', ADMIN_EMAIL)
                page.fill('input[type="password"], input[name="password"]', ADMIN_PASSWORD)
                page.click('button[type="submit"]')
                page.wait_for_load_state("networkidle", timeout=20000)

                # هدایت به بخش پیام‌های تماس با ما
                page.goto("https://aiabed.ir/admin/contacts?source=contact&status=unread", wait_until="networkidle", timeout=30000)

                cards = page.query_selector_all("div.rounded-2xl.border.p-5")
                logger.info(f"تعداد {len(cards)} پیام در پنل ادمین یافت شد.")

                for card in cards:
                    name_el = card.query_selector("span.font-semibold.text-slate-800")
                    phone_el = card.query_selector('p[dir="ltr"] span')
                    biz_el = card.query_selector("span.text-sm.text-slate-500")
                    msg_el = card.query_selector("p.text-sm.leading-6.text-slate-700")

                    name = name_el.inner_text().strip() if name_el else "مشتری"
                    phone = phone_el.inner_text().strip() if phone_el else ""
                    biz = biz_el.inner_text().replace("—", "").strip() if biz_el else ""
                    msg = msg_el.inner_text().strip() if msg_el else ""

                    c_key = f"{name}_{phone}"
                    if phone and c_key not in processed_ids:
                        new_contacts.append({
                            "id": c_key,
                            "name": name,
                            "phone": phone,
                            "business": biz,
                            "message": msg
                        })
                browser.close()
        except Exception as e:
            logger.error(f"خطای بررسی آنلاین: {e}")
    else:
        logger.warning("اطلاعات ورود ADMIN_EMAIL یا ADMIN_PASSWORD در Secrets تنظیم نشده است.")

    if not new_contacts:
        logger.info("✅ هیچ پیام جدیدی برای پردازش وجود ندارد.")
        return

    logger.info(f"🎯 تعداد {len(new_contacts)} پیام جدید نیازمند اقدام کشف شد.")

    for c in new_contacts:
        c_id = c["id"]
        name = c["name"]
        phone = c["phone"]
        biz = c["business"]
        norm_phone = normalize_iran_phone(phone)

        # تولید پاسخ هوشمند
        response_text, channel = generate_personalized_response(c)

        logger.info(f"ارتباط با {name} از کانال {channel}...")

        # آماده‌سازی لینک‌های اقدام سریع
        buttons = []
        if norm_phone:
            encoded_text = urllib.parse.quote(response_text)
            wa_url = f"https://web.whatsapp.com/send?phone={norm_phone}&text={encoded_text}"
            tg_url = f"https://t.me/+{norm_phone}"
            buttons.append([
                {"text": "💬 ارسال در واتساپ", "url": wa_url},
                {"text": "📲 گفتگو در تلگرام", "url": tg_url}
            ])

        # ارسال گزارش به تلگرام شخصی شما
        alert_body = (
            f"👤 *مشتری:* {name}\n"
            f"📞 *شماره تماس:* `{phone}`\n"
            f"💼 *حوزه فعالیت:* {biz}\n"
            f"🎯 *کانال ترجیحی:* {channel}\n\n"
            f"💬 *پاسخ پیشنهادی ایجنت:*\n_{response_text}_"
        )
        notify_owner_via_telegram(f"لید جدید از سایت aiabed.ir ({channel})", alert_body, buttons)

        save_processed_id(c_id)

    logger.info("پایان اجرای موفق دوره‌ای.")

if __name__ == "__main__":
    run_github_agent()
