import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- تنظیمات اتصال مستقیم Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# --- Gemini API (اختیاری جهت هوش مصنوعی پویا) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# --- اطلاعات تلگرام شخصی (@abedahm) ---
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE", "+989161002550")

# --- مسیرهای ذخیره لاگ و تاریخچه ---
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
HISTORY_FILE = DATA_DIR / "processed_contacts.json"
PHONE_LEADS_FILE = DATA_DIR / "phone_calls_todo.json"
