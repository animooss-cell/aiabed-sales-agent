import time
import urllib.parse
import logging
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright

from config import DATA_DIR, LOGS_DIR
from sender import normalize_iran_phone

logger = logging.getLogger("SalesAgent.WhatsAppAuto")
WHATSAPP_SESSION_DIR = DATA_DIR / "whatsapp_profile"

def send_whatsapp_message_auto(phone: str, text: str, headless: bool = False) -> bool:
    """
    ارسال کاملاً خودکار پیام در واتساپ وب با استفاده از سشن ذخیره شده
    """
    norm_phone = normalize_iran_phone(phone)
    if not norm_phone:
        logger.error(f"شماره معتبر نیست: {phone}")
        return False

    if not WHATSAPP_SESSION_DIR.exists():
        logger.error("پروفایل واتساپ هنوز ساخته نشده است. ابتدا setup_whatsapp.py را اجرا کنید.")
        return False

    encoded_text = urllib.parse.quote(text)
    url = f"https://web.whatsapp.com/send?phone={norm_phone}&text={encoded_text}"

    logger.info(f"در حال ارسال خودکار واتساپ به {norm_phone}...")

    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(WHATSAPP_SESSION_DIR),
                headless=headless
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=60000)

            # انتظار برای لود شدن دکمه ارسال (آیکون send) یا کادر ورودی
            logger.info("در حال انتظار برای لود چت و باکس ارسال...")
            send_btn = page.wait_for_selector('button span[data-icon="send"], [aria-label="Send"], [aria-label="ارسال"]', timeout=30000)

            if send_btn:
                time.sleep(2)  # تاخیر طبیعی انسانی
                send_btn.click()
                logger.info(f"✅ دکمه ارسال کلیک شد و پیام با موفقیت به {norm_phone} ارسال گردید.")
                time.sleep(3)  # مکث برای اطمینان از خروج پیام از شبکه
                context.close()
                return True
            else:
                # تلاش با کلید Enter در صورت عدم یافتن آیکون
                page.keyboard.press("Enter")
                time.sleep(3)
                context.close()
                return True
    except Exception as e:
        logger.error(f"خطا در ارسال خودکار واتساپ: {e}")
        return False

if __name__ == "__main__":
    # تست با یک پیام نمونه
    print("ماژول ارسال خودکار واتساپ وب آماده است.")
