import httpx
import logging
from typing import List, Dict, Any, Optional
from config import SUPABASE_URL, SUPABASE_ANON_KEY

logger = logging.getLogger("SalesAgent.Supabase")

class SupabaseContactClient:
    def __init__(self, base_url: str = SUPABASE_URL, anon_key: str = SUPABASE_ANON_KEY):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "apikey": anon_key,
            "Authorization": f"Bearer {anon_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def fetch_contacts(self, source: str = "contact", unread_only: bool = True) -> List[Dict[str, Any]]:
        """
        واکشی پیام‌ها از جدول contacts
        به صورت پیش‌فرض پیام‌های «تماس با ما» (source=contact) و خوانده‌نشده
        """
        url = f"{self.base_url}/rest/v1/contacts"
        params = {
            "select": "*",
            "order": "created_at.desc"
        }
        if source:
            params["source"] = f"eq.{source}"
        if unread_only:
            params["read"] = "eq.false"

        try:
            with httpx.Client(timeout=20.0) as client:
                res = client.get(url, headers=self.headers, params=params)
                if res.status_code == 200:
                    contacts = res.json()
                    logger.info(f"تعداد {len(contacts)} پیام از نوع '{source}' دریافت شد.")
                    return contacts
                else:
                    logger.error(f"خطا در واکشی مخاطبان: {res.status_code} - {res.text}")
                    return []
        except Exception as e:
            logger.error(f"خطای ارتباط با Supabase: {e}")
            return []

    def mark_as_read(self, contact_id: Any) -> bool:
        """
        تغییر وضعیت پیام به خوانده شده در دیتابیس
        """
        url = f"{self.base_url}/rest/v1/contacts"
        params = {"id": f"eq.{contact_id}"}
        payload = {"read": True}

        try:
            with httpx.Client(timeout=20.0) as client:
                res = client.patch(url, headers=self.headers, params=params, json=payload)
                if res.status_code in [200, 204]:
                    logger.info(f"پیام شناسه {contact_id} با موفقیت به عنوان خوانده شده ثبت شد.")
                    return True
                else:
                    logger.error(f"خطا در علامت‌گذاری خوانده شدن: {res.status_code} - {res.text}")
                    return False
        except Exception as e:
            logger.error(f"خطای مارک کردن پیام: {e}")
            return False
