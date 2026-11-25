import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from playwright.sync_api import sync_playwright

from config import DATA_DIR, LOGS_DIR

logger = logging.getLogger("SalesAgent.BrowserManager")
STATE_FILE = DATA_DIR / "browser_auth_state.json"

class BrowserContactManager:
    def __init__(self, headless: bool = True):
        self.headless = headless
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def fetch_contact_messages(self, unread_only: bool = True) -> List[Dict[str, Any]]:
        """
        واکشی پیام‌های فرم «تماس با ما» از پنل ادمین aiabed.ir با استفاده از مرورگر خودکار
        """
        results = []
        with sync_playwright() as p:
            # اگر سشن ذخیره شده باشد از آن استفاده می‌کند
            storage_state = str(STATE_FILE) if STATE_FILE.exists() else None
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(storage_state=storage_state)
            page = context.new_page()

            url = "https://aiabed.ir/admin/contacts?source=contact"
            if unread_only:
                url += "&status=unread"

            logger.info(f"در حال باز کردن صفحه پیام‌های تماس با ما: {url}")
            page.goto(url, wait_until="networkidle", timeout=30000)

            # اگر به صفحه لاگین ریدایرکت شد
            if "/admin/login" in page.url:
                logger.warning("نیاز به ورود به پنل ادمین وجود دارد.")
                email = os.getenv("ADMIN_EMAIL", "")
                password = os.getenv("ADMIN_PASSWORD", "")

                if email and password:
                    logger.info("در حال لاگین خودکار با اطلاعات تنظیم‌شده در .env...")
                    page.fill('input[type="email"], input[name="email"]', email)
                    page.fill('input[type="password"], input[name="password"]', password)
                    page.click('button[type="submit"]')
                    page.wait_for_load_state("networkidle", timeout=20000)
                    # ذخیره وضعیت سشن لاگین
                    context.storage_state(path=str(STATE_FILE))
                    page.goto(url, wait_until="networkidle", timeout=30000)
                else:
                    logger.error("اطلاعات ورود ADMIN_EMAIL یا ADMIN_PASSWORD در .env تنظیم نشده است.")
                    browser.close()
                    return []

            # استخراج کارت‌های پیام
            # سلکتور کارت‌های پیام: div.rounded-2xl.border.p-5
            cards = page.query_selector_all("div.rounded-2xl.border.p-5")
            logger.info(f"تعداد {len(cards)} کارت پیام در صفحه یافت شد.")

            for card in cards:
                try:
                    # نام
                    name_el = card.query_selector("span.font-semibold.text-slate-800")
                    name = name_el.inner_text().strip() if name_el else "نامشخص"

                    # شماره تلفن
                    phone_el = card.query_selector('p[dir="ltr"] span')
                    phone = phone_el.inner_text().strip() if phone_el else ""

                    # ایمیل
                    email_p = card.query_selector('p[dir="ltr"]')
                    email_text = email_p.inner_text().strip() if email_p else ""
                    email = ""
                    if email_text and "@" in email_text:
                        # حذف شماره از متن برای به دست آوردن ایمیل خالص
                        email = email_text.replace(phone, "").strip()

                    # کسب‌وکار / سرفصل
                    biz_el = card.query_selector("span.text-sm.text-slate-500")
                    business = biz_el.inner_text().replace("—", "").strip() if biz_el else ""

                    # متن پیام
                    msg_el = card.query_selector("p.text-sm.leading-6.text-slate-700")
                    message = msg_el.inner_text().strip() if msg_el else ""

                    # تاریخ
                    date_el = card.query_selector("p.mt-3.text-xs.text-slate-400")
                    date_str = date_el.inner_text().strip() if date_el else ""

                    # بررسی وضعیت خوانده شده
                    read_checkbox = card.query_selector('input[type="checkbox"]:has-text("خوانده شد"), label:has-text("خوانده شد") input')
                    is_read = read_checkbox.is_checked() if read_checkbox else False

                    contact_data = {
                        "name": name,
                        "phone": phone,
                        "email": email,
                        "business": business,
                        "message": message,
                        "date": date_str,
                        "read": is_read
                    }
                    results.append(contact_data)
                except Exception as e:
                    logger.warning(f"خطا در پارس کردن یک پیام: {e}")

            browser.close()
            return results
