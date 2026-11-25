import os
import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

from config import DATA_DIR, LOGS_DIR

logger = logging.getLogger("SalesAgent.WhatsAppSetup")
WHATSAPP_SESSION_DIR = DATA_DIR / "whatsapp_profile"

def setup_whatsapp_session():
    """
    راه‌اندازی اولیه و اسکن کد QR واتساپ وب
    سشن برای همیشه در این پوشه ذخیره می‌شود تا ایجنت بتواند خودکار پیام بفرستد.
    """
    WHATSAPP_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 65)
    print("📱 در حال باز کردن مرورگر واتساپ وب جهت اتصال اولیه...")
    print("لطفاً در گوشی خود:")
    print("۱. واتساپ را باز کنید.")
    print("۲. به تنظیمات (Settings) -> دستگاه‌های متصل (Linked Devices) بروید.")
    print("۳. دکمه Link a Device را بزنید و کد QR روی صفحه را اسکن کنید.")
    print("=" * 65)

    with sync_playwright() as p:
        # استفاده از پروفایل پایدار (Persistent Context) جهت ماندگاری دائمی لاگین
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(WHATSAPP_SESSION_DIR),
            headless=False,  # باز شدن مرورگر تا کد QR را ببینید
            args=["--start-maximized"]
        )
        page = context.new_page()
        page.goto("https://web.whatsapp.com")

        print("\n⏳ منتظر اسکن QR کد توسط شما... (پس از ورود چت‌ها ظاهر می‌شوند)")

        # انتظار تا زمان لاگین شدن و لود شدن لیست چت‌ها
        try:
            page.wait_for_selector('div[contenteditable="true"], div[data-tab="3"], [aria-label*="Chat list"], [aria-label*="لیست گفتگو"]', timeout=180000)
            print("\n✅ فوق‌العاده! واتساپ شما با موفقیت متصل و سشن ذخیره شد.")
            print("از این پس ایجنت می‌تواند به صورت خودکار پیام‌ها را ارسال کند.")
            time.sleep(3)
        except Exception:
            print("\n⚠️ زمان انتظار به پایان رسید یا هنوز اسکن کامل نشده است.")

        context.close()

if __name__ == "__main__":
    setup_whatsapp_session()
