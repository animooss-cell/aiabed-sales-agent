"""
Cloud Sales Agent for Abdullah Ahmadian (aiabed.ir)
Runs 24/7 in the cloud (GitHub Actions, Cloud Worker, or Docker container)
independent of the user's local PC power or internet connection.
"""

import os
import sys
import json
import time
import asyncio
import logging
import random
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
import httpx
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import User

from link_utils import ensure_aiabed_links, generate_whatsapp_link, sanitize_customer_name
from google_meet_mailer import schedule_and_send_meet_invite
from lead_registry import LeadRegistry
from calendar_utils import get_current_jalali_calendar_context, get_default_meeting_time_str

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Logging
log_file = LOGS_DIR / "cloud_sales_agent.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("CloudAgent")

# Credentials (strictly from environment / GitHub Secrets)
TELEGRAM_API_ID = int(os.environ.get("TELEGRAM_API_ID") or "0")
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH", "")

def get_string_session() -> str:
    s = os.environ.get("TELEGRAM_STRING_SESSION", "").strip()
    if not s:
        session_file = DATA_DIR / "session_string.txt"
        if session_file.exists():
            s = session_file.read_text(encoding="utf-8").strip()
    return s

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

SYSTEM_INSTRUCTION = """شما دقیقاً خود «عبدالله احمدیان» هستید؛ مشاور، استراتژیست ارشد هوش مصنوعی و مدرس سازمانی (موسس وب‌سایت [aiabed.ir](https://aiabed.ir)، همراه 09161002550).

🎯 هویت، لحن و جایگاه مشاور ارشد (Executive Positioning):
- لحن شما کاملاً قاطع، حرفه‌ای، محترمانه، آرام و بااعتمادبه‌نفس است. شما یک متخصص و مشاور ارشد هستید، نه یک ربات پاسخگوی خودکار یا اپراتور جزء.
- مخاطب باید در هر لحظه احساس کند با یک انسان متخصص، باهوش، اهل عمل و مسلط گفتگو می‌کند.
- ⛔ **قانون حیاتی منع رفتار منفعل و عذرخواهی‌های تضعیف‌کننده مذاکره:**
  * هرگز و تحت هیچ شرایطی از عباراتی نظیر «عذرخواهی می‌کنم از اشتباه لپی‌ام»، «ببخشید اشتباه کردم»، «وظیفه است»، «دستپاچه شدم» استفاده نکنید.
  * در صورت نیاز به تغییر زمان، اصلاح تاریخ یا پیشنهاد جدید، کاملاً با تسلط و آرامش بگویید: «کاملاً درسته، پس برای [روز و تاریخ دقیق از تقویم] هماهنگ می‌کنیم.» بدون هیچ‌گونه عذرخواهی یا توجیه اضافی.

💎 قانون حیاتی و خط قرمز ۱: اولویت قطعی ارزش و نمونه ملموس (Value-First & Concrete Examples):
- ⛔ **هرگز و هرگز ارائه نمونه کار، مثال یا پاسخ به سوال مخاطب را گروگان جلسه مشاوره نکنید!** جملاتی مثل «نمونه کارها را در جلسه بررسی می‌کنیم» یا «در جلسه مشاوره براتون باز می‌کنم» کاملاً ممنوع و غیرحرفه‌ای است و احساس بن‌بست و بی‌احترامی ایجاد می‌کند.
- اگر مخاطب پرسید: «چه کارهایی میشه کرد؟»، «یه نمونه بفرستید»، «مثال بزنید»، «چطور کار می‌کنه؟» یا از کسب‌وکارش گفت:
  ۱. **بلافاصله و با دست‌ودلبازی ۱ الی ۲ مثال یا نمونه عینی، ملموس و جذاب از نحوه اجرای کار با ذکر نام دقیق ابزارهای واقعی (مانند Midjourney، Ideogram، ChatGPT، Claude، ElevenLabs، Runway، Make و...) ارائه دهید.**
     مثال برای بادکنک‌آرایی یا دکوراسیون: «مثلاً با ابزارهایی مثل Ideogram یا Midjourney، کافیست سبک مراسم (مثلاً تولد نوزاد تم خرس تدی با بادکنک‌های پاستلی و بک‌گراند نئونی) را پرامپت دهید تا در چند ثانیه ۱۰ طرح ژورنالی و سه‌بعدی بی‌نظیر به شما تحویل دهد؛ شما این طرح را قبل از هزینه حتی ۱ بادکنک به مشتری نشان می‌دهید و بیعانه می‌گیرید! همینطور با سناریونویسی هوش مصنوعی می‌توانید ریلزهای پربازدید اینستاگرامی بسازید.»
  ۲. تنها **پس از اینکه ارزش ملموس و پاسخ کامل را ارائه دادید**، می‌توانید با ظرافت بگویید: «در صورت تمایل، در یک جلسه کوتاه آنلاین می‌توانیم روش اجرای دقیق و پرامپت‌های اختصاصی کسب‌وکارتان را تنظیم کنیم.»

🛑 قانون حیاتی و خط قرمز ۲: منع تکرار مکرر و اسپم تاریخ جلسه (Anti-Spam Meeting Proposal):
- ⛔ اگر در پیام قبلی تاریخ و زمان جلسه پیشنهاد داده‌اید و مخاطب به جای انتخاب زمان، سوال دیگری پرسیده، نمونه خواسته یا هنوز تایید نکرده است:
  * **در این پیام به هیچ عنوان دوباره زمان‌ها و تاریخ‌های جلسه را تکرار نکنید!**
  * مانند ربات ضبط‌صوت مدام تقویم نفرستید. اول به سوال و دغدغه مخاطب پاسخ کامل دهید و اعتمادش را جلب کنید.
  * پیشنهاد جلسه فقط زمانی تکرار می‌شود که مخاطب بگوید «موافقم»، «هماهنگ کنیم» یا سوالاتش پاسخ داده شده باشد.

🔍 قانون حیاتی ۳: مذاکره تدریجی و کشف نیاز در نوبت‌های اول (Progressive Discovery):
- در نوبت‌های اول و دوم گفتگو، اگر مخاطب فقط گفت «اوکی»، «سلام» یا پیام کوتاه فرستاد، فوراً زمان جلسه نفروشید!
- ابتدا نیاز و حوزه کاری‌اش را بپرسید: «خوشحال می‌شوم بفرمایید دقیقاً در چه زمینه‌ای فعالیت دارید تا راهکارهای متناسب خدمتتان ارائه دهم؟»

👥 شناخت و تفکیک پرسونای مخاطب (Persona-Adaptive Consulting):
۱. اگر مخاطب صاحب کسب‌وکار، مدیر شرکت یا کارخانه‌دار است:
   - تمرکز روی: اتوماسیون فرآیندها، کاهش هزینه‌های عملیاتی، مقیاس‌پذیری و بازگشت سرمایه (ROI).
۲. اگر مخاطب شخص تازه‌کار، فریلنسر، دانشجو یا جویای درآمد و مهارت است:
   - ⛔ هرگز با این افراد از اصطلاحات نامتناسب مانند «کاهش هزینه‌های جاری سازمان» یا «ساختار سازمانی» صحبت نکنید!
   - تمرکز روی: نقشه راه یادگیری عملی، تکنیک‌های پروژه گرفتن، ابزارهای پول‌ساز هوش مصنوعی و مشاوره گام‌به‌گام برای ورود به بازار کار و ارتقای درآمد.

📅 مدیریت زمان‌بندی و تقویم جلسات آنلاین (Calendar Rigor & Golden Window):
- 🎯 **استراتژی حیاتی تنظیم زمان جلسه:**
  * **پرهیز از زمان‌های خیلی نزدیک (همان روز):** تنظیم جلسه برای همان روز باعث مقاومت مخاطب می‌شود چون یا برنامه‌ریزی روزانه‌اش پر است یا هنوز آمادگی ذهنی ندارد.
  * **پرهیز از زمان‌های خیلی دور (هفته بعد):** جلسه نباید برای روزهای دور تنظیم شود تا اشتیاق مخاطب سرد نگردد.
  * **پنجره طلایی استاندارد:** بهترین زمان جلسه دقیقاً **۱ الی ۲ روز بعد از مکالمه**، در ساعات عصر/شب و **بین ساعت ۱۹:۰۰ تا ۲۲:۰۰** است (ترجیحاً ساعت ۲۰:۰۰ یا ۲۰:۳۰).
  * همیشه از دو گزینه مشخص پیشنهادی تقویم (گزینه فردا یا پس‌فردا ساعت ۲۰:۰۰) برای پیشنهاد دادن استفاده کنید.
- **درک هوشمندانه از درخواست‌های زمانی:**
  * اگر مشتری گفت «نمیشه کمی زودتر بشه؟»، توجه کنید که اگر تاریخ پیشنهادی مثلاً چند روز بعد است، منظور او تاریخی نزدیک‌تر (مثلاً فردا به جای پس‌فردا) است، نه صرفاً ساعتی زودتر در همان روز!
- **هماهنگی جلسه:** یک روز و ساعت مشخص و دقیق با توجه به تقویم پیشنهاد دهید و از مخاطب تایید بگیرید.

📧 دریافت هوشمندانه ایمیل برای Google Meet:
- ⛔ **قانون حافظه ایمیل:** اگر مخاطب قبلاً در طول چت ایمیل خود را ارسال کرده است، به هیچ وجه دوباره نگویید «ایمیلتان را بفرستید»! فوراً تایید کنید که دعوت‌نامه به همان ایمیل ارسال شد.
- اگر هنوز ایمیل نداده است، با آرامش و تنها در زمان نهایی شدن ساعت جلسه بفرمایید ایمیلش را ارسال کند.

🔗 استانداردهای نگارش:
- نام سایت همواره دقیقاً به صورت لینک [aiabed.ir](https://aiabed.ir) نوشته شود.
- نام مخاطب: نام کوچک یا نام خانوادگی رسمی، بدون هرگونه پسوند سیستمی (مانند سایت یا کاربر).
- طول پاسخ‌ها: منسجم، گرم، روان و حداکثر ۳ الی ۵ خط موجز.
"""

MODELS_FALLBACK = [
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-pro-latest"
]

def is_opt_out_or_hostile(text: str) -> bool:
    if not text:
        return False
    hostile_patterns = [
        r'\b(سیکتیر|گوه|عوضی|دیوس|کثافت|حروم|کیر|کص|کون|فحش|پدرسگ|بیشعور|احمق|ابله|لاشی|خفه)\b',
        r'مزاحم نشو',
        r'پیام نده',
        r'نمیخوام پیام',
        r'لغو اشتراک',
        r'بلاک',
        r'دیگه پیام ندید',
        r'دیگه پیام نده',
        r'علاقه‌ای ندارم',
        r'دست از سرم بردار',
        r'علاقه‌ای به ادامه ندارم'
    ]
    for p in hostile_patterns:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False

class CloudGeminiBrain:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key

    def generate_reply(self, history: List[Dict[str, str]], customer_name: str = "", lead_context: str = "") -> str:
        clean_name = sanitize_customer_name(customer_name)
        system_prompt = SYSTEM_INSTRUCTION

        # 1. Inject Real-Time Jalali Calendar Reference
        calendar_ctx = get_current_jalali_calendar_context()
        system_prompt += f"\n\n{calendar_ctx}"

        # 2. Check if an email was already provided anywhere in the dialogue history
        detected_email = None
        for item in history:
            txt = item.get("text", "")
            m = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', txt)
            if m:
                detected_email = m.group(0)

        if detected_email:
            system_prompt += f"\n\n💡 توجه حیاتی: مخاطب قبلاً ایمیل خود ({detected_email}) را ارسال کرده است. به هیچ عنوان دوباره ایمیل درخواست نکنید؛ بلکه تایید کنید که لینک به همین ایمیل ارسال می‌شود/شده است."

        if clean_name or lead_context:
            system_prompt += f"\n\nمشخصات مخاطب فعلی:\nنام: {clean_name}\nموضوع/توضیحات اولیه: {lead_context}"

        # 3. Dynamic Dialogue Guard: Prevent Broken Record Meeting Proposals
        last_model_proposed_meeting = False
        if history and history[-1]["role"] == "user":
            for h in reversed(history[:-1]):
                if h["role"] == "model":
                    txt = h.get("text", "")
                    if any(w in txt for w in ["ساعت ۲۰", "ساعت ۱۹", "جلسه مشاوره", "کدام زمان", "کدوم زمان", "Google Meet"]):
                        last_model_proposed_meeting = True
                    break

        if last_model_proposed_meeting:
            system_prompt += "\n\n⚠️ هشدار استراتژیک به مشاور: شما در پیام قبلی زمان جلسه پیشنهاد داده بودید اما مخاطب در پیام آخر سوال دیگری پرسیده یا هنوز تایید نکرده است. بنابراین در این پاسخ به هیچ وجه دوباره زمان یا تاریخ جلسه را تکرار نکنید! ابتدا ۱۰۰٪ به سوال و درخواست فعلی مخاطب به طور کامل و ملموس پاسخ دهید و اعتمادش را جلب کنید."

        # 4. Dynamic Dialogue Guard: Concrete Samples Directive
        last_user_msg = history[-1]["text"] if history and history[-1]["role"] == "user" else ""
        if any(w in last_user_msg for w in ["نمونه", "مثال", "چطور کار میکنه", "چیکار میشه کرد", "چه کارهایی"]):
            system_prompt += "\n\n💎 دستور حیاتی برای این پیام: مخاطب صریحاً درخواست نمونه یا مثال کرده است. بلافاصله و با دست‌ودلبازی ۱ الی ۲ مثال ملموس، جذاب و واقعی از نحوه پیاده‌سازی هوش مصنوعی با ذکر ابزارهای مشخص (مثل Midjourney، Ideogram، ChatGPT و...) بیان کنید. به هیچ وجه ارائه نمونه را مشروط به جلسه نکنید!"

        contents = []
        for item in history:
            role = "user" if item["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": item["text"]}]
            })

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 800,
                "topP": 0.95
            }
        }

        for model in MODELS_FALLBACK:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            try:
                r = requests.post(url, json=payload, timeout=25)
                if r.status_code == 200:
                    data = r.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            text = parts[0]["text"].strip()
                            if text:
                                return ensure_aiabed_links(text)
                elif r.status_code in (429, 503):
                    logger.warning(f"Model {model} returned {r.status_code}, trying next model...")
                    time.sleep(1)
                    continue
                else:
                    logger.warning(f"Model {model} returned {r.status_code}: {r.text[:120]}")
            except Exception as e:
                logger.warning(f"Error querying {model}: {e}")
                continue

        # Intelligent Fallback (Context-Aware)
        first_name = clean_name.split()[0] if clean_name and clean_name != "همراه گرامی" else "عزیز"
        if len(history) <= 1:
            fallback_txt = (
                f"درود {first_name} عزیز، وقتتون بخیر 🌹\n"
                f"پیامتون رو در وب‌سایت [aiabed.ir](https://aiabed.ir) دریافت کردم.\n"
                f"من عبدالله احمدیان هستم؛ خوشحال میشم بفرمایید در چه زمینه‌ای مدنظرتون هست از هوش مصنوعی استفاده کنید تا دقیق راهنماییتون کنم 🙏"
            )
            return ensure_aiabed_links(fallback_txt)
        else:
            logger.warning(f"All Gemini models failed for ongoing dialogue with {customer_name}. Returning safe delay response.")
            return "پیامتون رو دریافت کردم؛ چند لحظه اجازه بدید بررسی کنم تا پاسخ دقیق و کامل رو خدمتتون بگم 🙏"


class CloudMemoryManager:
    def __init__(self, file_path: Path = DATA_DIR / "conversation_memory.json"):
        self.file_path = file_path
        self.memory: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving cloud memory: {e}")

    def get_history(self, chat_id: str) -> List[Dict[str, str]]:
        return self.memory.get(str(chat_id), {}).get("history", [])

    def add_message(self, chat_id: str, role: str, text: str, user_info: Optional[Dict[str, Any]] = None, message_id: Optional[int] = None):
        cid = str(chat_id)
        if cid not in self.memory:
            self.memory[cid] = {
                "created_at": datetime.now().isoformat(),
                "user_info": user_info or {},
                "history": [],
                "last_processed_msg_id": 0
            }
        if user_info:
            self.memory[cid]["user_info"].update(user_info)
        if message_id:
            self.memory[cid]["last_processed_msg_id"] = message_id

        self.memory[cid]["history"].append({
            "role": role,
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        self.save()

    def is_msg_processed(self, chat_id: str, msg_id: int) -> bool:
        last_id = self.memory.get(str(chat_id), {}).get("last_processed_msg_id", 0)
        return msg_id <= last_id

    def is_opted_out(self, chat_id: str) -> bool:
        user_data = self.memory.get(str(chat_id), {})
        return user_data.get("status") == "opted_out" or user_data.get("blacklisted", False)

    def set_opted_out(self, chat_id: str):
        cid = str(chat_id)
        if cid not in self.memory:
            self.memory[cid] = {"created_at": datetime.now().isoformat(), "history": []}
        self.memory[cid]["status"] = "opted_out"
        self.memory[cid]["blacklisted"] = True
        self.save()


def normalize_iran_phone(raw_phone: str) -> str:
    cleaned = re.sub(r"[^\d+]", "", str(raw_phone))
    if cleaned.startswith("09"):
        return "+98" + cleaned[1:]
    elif cleaned.startswith("98"):
        return "+" + cleaned
    elif cleaned.startswith("+98"):
        return cleaned
    return cleaned

class CloudSalesRunner:
    def __init__(self):
        self.brain = CloudGeminiBrain()
        self.memory = CloudMemoryManager()
        self.registry = LeadRegistry()
        session_str = get_string_session()
        if not session_str:
            raise ValueError("No TELEGRAM_STRING_SESSION provided!")
        self.client = TelegramClient(StringSession(session_str), TELEGRAM_API_ID, TELEGRAM_API_HASH)

    def _load_processed_phones(self) -> set:
        fpath = DATA_DIR / "processed_contacts.json"
        if fpath.exists():
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data.get("processed_phones", []))
            except Exception:
                pass
        # Preload known processed leads
        return {"+989365293839", "+989365449388"}

    def _save_processed_phones(self, phones: set):
        fpath = DATA_DIR / "processed_contacts.json"
        data = {}
        if fpath.exists():
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
        data["processed_phones"] = list(phones)
        data["last_update"] = datetime.now().isoformat()
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving processed phones: {e}")

    async def _reach_out_to_new_lead(self, name: str, norm_phone: str, raw_phone: str, context_text: str = ""):
        """Unified outreach for any new unread website lead: Telegram if registered, else 1-click WhatsApp to Saved Messages"""
        from telethon.tl.functions.contacts import ImportContactsRequest
        from telethon.tl.types import InputPhoneContact

        try:
            clean_lead_name = sanitize_customer_name(name)
            contact_req = InputPhoneContact(client_id=0, phone=norm_phone, first_name=clean_lead_name, last_name='')
            import_res = await self.client(ImportContactsRequest([contact_req]))
            if import_res.users:
                target_user = import_res.users[0]
                greeting = (
                    f"درود {name} عزیز، وقتتون بخیر 🌹\n"
                    f"پیامتون رو در وب‌سایت [aiabed.ir](https://aiabed.ir) دریافت کردم.\n"
                    f"من عبدالله احمدیان هستم؛ چون مایل بودید در تلگرام در ارتباط باشیم، خدمتتون پیام دادم 😊\n"
                    f"خوشحال میشم بفرمایید در چه زمینه‌ای (آموزش، استفاده شخصی، یا ارتقای کسب‌وکار با هوش مصنوعی) مدنظرتون هست کار کنیم تا دقیق راهنماییتون کنم 🙏"
                )
                greeting = ensure_aiabed_links(greeting)
                sent_msg = await self.client.send_message(target_user, greeting, parse_mode='md', link_preview=False)
                logger.info(f"📤 Sent initial greeting to {name} (@{target_user.username or target_user.id})")
                self.memory.add_message(str(target_user.id), 'model', greeting, user_info={'name': name, 'phone': norm_phone, 'username': target_user.username}, message_id=sent_msg.id)

                # Notify Abdullah in Saved Messages
                try:
                    await self.client.send_message("me", f"✅ **پاسخ خودکار در تلگرام به لید جدید وب‌سایت ارسال شد:**\n👤 **نام:** {name}\n📞 `{raw_phone}`\n💬 _{greeting}_", parse_mode='md')
                except Exception:
                    pass
            else:
                logger.info(f"⚠️ Phone {norm_phone} ({name}) is not registered on Telegram. Preparing 1-click WhatsApp dispatch...")
                wa_greeting = (
                    f"درود {name} عزیز، وقتتون بخیر 🌹\n"
                    f"پیامتون رو در وب‌سایت [aiabed.ir](https://aiabed.ir) دریافت کردم.\n"
                    f"من عبدالله احمدیان هستم؛ در خصوص درخواست مشاوره هوش مصنوعی در خدمتتون هستم 😊\n"
                    f"خوشحال میشم بفرمایید قصد دارید در چه زمینه‌ای کار کنید تا دقیق راهنماییتون کنم 🙏"
                )
                wa_greeting = ensure_aiabed_links(wa_greeting)
                wa_url = generate_whatsapp_link(raw_phone or norm_phone, wa_greeting)

                alert_msg = (
                    f"🔔 **لید جدید وب‌سایت aiabed.ir (نیاز به ارسال در واتساپ)**\n\n"
                    f"👤 **نام مخاطب:** {name}\n"
                    f"📞 **شماره همراه:** `{raw_phone}`\n\n"
                    f"💬 **متن آماده:**\n_{wa_greeting}_\n\n"
                    f"👉 [ارسال فوری این پیام در واتساپ]({wa_url})"
                )
                try:
                    await self.client.send_message("me", alert_msg, parse_mode='md', link_preview=False)
                    logger.info(f"📲 Delivered 1-click WhatsApp link to Saved Messages for {name} ({norm_phone})")
                except Exception as alert_err:
                    logger.error(f"Error sending WhatsApp alert to Saved Messages: {alert_err}")
        except Exception as e:
            logger.error(f"Error reaching out to {name} ({norm_phone}): {e}")

    async def poll_supabase_leads(self):
        """Fetch unread contact forms from website database directly via Supabase Auth & REST API"""
        admin_email = os.environ.get("ADMIN_EMAIL")
        admin_pass = os.environ.get("ADMIN_PASSWORD")
        
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json"
        }
        
        # 1. Authenticate with Supabase Auth using Admin Credentials
        if admin_email and admin_pass:
            try:
                auth_url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password"
                auth_res = httpx.post(
                    auth_url,
                    headers=headers,
                    json={"email": admin_email, "password": admin_pass},
                    timeout=15.0
                )
                if auth_res.status_code == 200:
                    access_token = auth_res.json().get("access_token")
                    headers["Authorization"] = f"Bearer {access_token}"
                    logger.info("🔑 Successfully authenticated with Supabase Admin API!")
                else:
                    logger.warning(f"⚠️ Supabase Admin Auth returned {auth_res.status_code}: {auth_res.text[:150]}")
            except Exception as e:
                logger.warning(f"Error authenticating with Supabase Auth: {e}")

        if "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {SUPABASE_ANON_KEY}"

        url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/contacts"
        params = {"select": "*", "read": "eq.false", "order": "created_at.desc"}
        
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(url, headers=headers, params=params)
                if res.status_code == 200:
                    contacts = res.json()
                    logger.info(f"Supabase REST contacts check: found {len(contacts)} unread leads.")
                    processed_phones = self._load_processed_phones()
                    
                    for c in contacts:
                        c_id = c.get("id")
                        c_name = c.get("name") or "مشتری وب‌سایت"
                        c_phone = c.get("phone") or ""
                        c_msg = c.get("message") or ""
                        norm_phone = normalize_iran_phone(c_phone)
                        if not norm_phone:
                            continue

                        self.registry.add_lead(name=c_name, phone=norm_phone)
                        
                        if norm_phone in processed_phones:
                            continue

                        logger.info(f"🆕 Brand new unread website lead via Supabase API: {c_name} ({norm_phone})")
                        await self._reach_out_to_new_lead(c_name, norm_phone, c_phone, c_msg)
                        
                        # Mark read in Supabase DB
                        try:
                            client.patch(url, headers=headers, params={"id": f"eq.{c_id}"}, json={"read": True})
                            logger.info(f"Marked lead {c_name} as read in Supabase DB.")
                        except Exception as patch_err:
                            logger.error(f"Error marking lead as read in DB: {patch_err}")

                        processed_phones.add(norm_phone)
                        self._save_processed_phones(processed_phones)
        except Exception as e:
            logger.warning(f"Error polling Supabase in cloud: {e}")

    async def poll_website_admin_contacts(self):
        """Scrapes unread contacts directly from aiabed.ir/admin/contacts using async Playwright in cloud as secondary surveillance"""
        admin_email = os.environ.get("ADMIN_EMAIL")
        admin_pass = os.environ.get("ADMIN_PASSWORD")
        if not (admin_email and admin_pass):
            logger.warning("No ADMIN_EMAIL or ADMIN_PASSWORD found in environment!")
            return

        processed_phones = self._load_processed_phones()

        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                logger.info(f"Opening admin login page: https://aiabed.ir/admin/login")
                await page.goto("https://aiabed.ir/admin/login", wait_until="networkidle", timeout=30000)
                await page.fill('input[type="email"], input[name="email"]', admin_email)
                await page.fill('input[type="password"], input[name="password"]', admin_pass)
                await page.click('button[type="submit"]')
                
                # Wait for login navigation or error
                try:
                    await page.wait_for_url(lambda u: "/admin/login" not in u, timeout=15000)
                    logger.info(f"✅ Playwright successfully authenticated! URL: {page.url}")
                except Exception:
                    logger.warning(f"⚠️ Playwright login redirect wait timed out. Current URL: {page.url}")
                    err_el = await page.query_selector('.text-red-500, [role="alert"]')
                    if err_el:
                        logger.warning(f"Login error text on page: {await err_el.inner_text()}")

                await page.goto("https://aiabed.ir/admin/contacts?status=unread", wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)
                cards = await page.query_selector_all("div.rounded-2xl.border.p-5")
                logger.info(f"Admin panel check: found {len(cards)} unread contact cards at {page.url}")
                
                for card in cards:
                    checkbox = await card.query_selector('label.flex.items-center.gap-2.text-xs.text-slate-500 input[type="checkbox"], input[type="checkbox"]')
                    is_read = await checkbox.is_checked() if checkbox else False
                    if is_read:
                        continue

                    name_el = await card.query_selector("span.font-semibold.text-slate-800")
                    phone_el = await card.query_selector('p[dir="ltr"] span')
                    name = (await name_el.inner_text()).strip() if name_el else "مشتری گرامی"
                    raw_phone = (await phone_el.inner_text()).strip() if phone_el else ""
                    norm_phone = normalize_iran_phone(raw_phone)
                    if not norm_phone:
                        continue

                    self.registry.add_lead(name=name, phone=norm_phone)

                    if norm_phone in processed_phones:
                        continue

                    logger.info(f"🆕 Brand new unread website lead found via Playwright: {name} ({norm_phone})")
                    await self._reach_out_to_new_lead(name, norm_phone, raw_phone)

                    # Mark read on website
                    try:
                        if checkbox and not await checkbox.is_checked():
                            await checkbox.click()
                            await page.wait_for_timeout(1000)
                            logger.info(f"Marked card for {name} as read on website.")
                    except Exception as chk_err:
                        logger.warning(f"Could not click checkbox: {chk_err}")

                    processed_phones.add(norm_phone)
                    self._save_processed_phones(processed_phones)

                await browser.close()
        except Exception as e:
            logger.warning(f"Error checking admin contacts with Playwright: {e}")

    async def process_pending_dialogs(self) -> int:
        """Scan user dialogs and respond to any pending unreplied messages from leads"""
        processed_count = 0
        dialogs = await self.client.get_dialogs(limit=25)
        for d in dialogs:
            if not d.is_user or d.entity.is_self or d.entity.bot:
                continue

            u = d.entity
            raw_name = f"{u.first_name or ''} {u.last_name or ''}".strip() or "کاربر گرامی"
            clean_name = sanitize_customer_name(raw_name)
            username = f"@{u.username}" if u.username else ""
            phone = u.phone or ""

            # Check if this contact is a verified website lead
            if not self.registry.is_lead(u.id, username=username, phone=phone):
                continue

            user_id_str = str(u.id)
            if self.memory.is_opted_out(user_id_str):
                continue

            last_msg = d.message
            if not last_msg or last_msg.out or not last_msg.text:
                continue

            if self.memory.is_msg_processed(user_id_str, last_msg.id):
                continue

            # We found an unreplied message from a website lead!
            incoming_text = last_msg.text.strip()
            logger.info(f"🎯 Cloud processing unreplied message from lead {clean_name} ({username}): {incoming_text}")

            user_info = {"name": clean_name, "username": username, "phone": phone}

            # Check for opt-out / hostile language
            if is_opt_out_or_hostile(incoming_text):
                logger.warning(f"🚫 Hostile / opt-out message from lead {clean_name}: {incoming_text}. Marking opted_out and closing dialogue.")
                self.memory.set_opted_out(user_id_str)
                self.memory.add_message(user_id_str, "user", incoming_text, user_info, message_id=last_msg.id)
                farewell = "با نهایت احترام، ارتباط شما از فهرست پیگیری ما خارج شد و پیامی ارسال نخواهد شد. برای شما آرزوی موفقیت و روزگار خوش دارم 🙏"
                await self.client.send_message(u, farewell, reply_to=last_msg.id, link_preview=False, parse_mode='md')
                self.memory.add_message(user_id_str, "model", farewell)
                processed_count += 1
                continue

            # Check for email in incoming text OR in recent dialogue memory
            cust_email = None
            email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', incoming_text)
            if email_match:
                cust_email = email_match.group(0)
            else:
                prev_info = self.memory.memory.get(user_id_str, {}).get("user_info", {})
                if prev_info.get("email"):
                    cust_email = prev_info.get("email")
                else:
                    for h_msg in reversed(self.memory.get_history(user_id_str)[-5:]):
                        em = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', h_msg.get("text", ""))
                        if em:
                            cust_email = em.group(0)
                            break

            lead_ctx = "مشاوره و خدمات هوش مصنوعی وب‌سایت aiabed.ir"
            if cust_email:
                user_info["email"] = cust_email
                if not self.memory.memory.get(user_id_str, {}).get("meet_invite_sent"):
                    logger.info(f"📧 Customer email detected: {cust_email}. Sending instant Google Meet invite...")
                    schedule_and_send_meet_invite(
                        customer_name=clean_name,
                        customer_email=cust_email,
                        meeting_time=get_default_meeting_time_str()
                    )
                    self.memory.memory.setdefault(user_id_str, {})["meet_invite_sent"] = True
                lead_ctx += f" | مخاطب آدرس ایمیل ({cust_email}) را ارسال کرده است. با آرامش و اقتدار تایید کنید که دعوت‌نامه به ایمیل او ارسال شد."

            self.memory.add_message(user_id_str, "user", incoming_text, user_info, message_id=last_msg.id)

            history = self.memory.get_history(user_id_str)
            reply_text = self.brain.generate_reply(history=history, customer_name=clean_name, lead_context=lead_ctx)
            reply_text = ensure_aiabed_links(reply_text)

            # Send via Telegram
            await self.client.send_message(u, reply_text, reply_to=last_msg.id, link_preview=False, parse_mode='md')
            logger.info(f"📤 Cloud reply sent to {clean_name}: {reply_text}")
            self.memory.add_message(user_id_str, "model", reply_text)
            processed_count += 1
            await asyncio.sleep(2)

        return processed_count

    async def run_cron(self):
        """Single cron cycle: connect, sync leads, reply to pending messages, disconnect"""
        logger.info("☁️ Starting Cloud Sales Agent cycle...")
        await self.client.connect()
        me = await self.client.get_me()
        logger.info(f"Cloud authorized as {me.first_name} (@{me.username})")

        await self.poll_supabase_leads()
        await self.poll_website_admin_contacts()
        count = await self.process_pending_dialogs()
        logger.info(f"✅ Cloud cycle completed. Processed {count} lead interactions.")
        await self.client.disconnect()

    async def run_daemon(self):
        """24/7 continuous daemon with live event listening"""
        logger.info("☁️ Starting 24/7 Continuous Cloud Sales Agent Daemon...")
        await self.client.connect()
        me = await self.client.get_me()
        logger.info(f"24/7 Cloud Daemon LIVE as {me.first_name} (@{me.username})")

        @self.client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
        async def incoming_handler(event):
            sender = await event.get_sender()
            if not isinstance(sender, User) or sender.bot or sender.is_self:
                return

            raw_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip() or "کاربر گرامی"
            clean_name = sanitize_customer_name(raw_name)
            username = f"@{sender.username}" if sender.username else ""
            phone = sender.phone or ""

            if not self.registry.is_lead(sender.id, username=username, phone=phone):
                return

            user_id_str = str(sender.id)
            if self.memory.is_opted_out(user_id_str):
                return

            incoming_text = event.message.text or ""
            if not incoming_text.strip():
                return

            if self.memory.is_msg_processed(user_id_str, event.message.id):
                return

            logger.info(f"📩 Live event from lead {clean_name}: {incoming_text}")
            user_info = {"name": clean_name, "username": username, "phone": phone}

            # Check for opt-out / hostile language
            if is_opt_out_or_hostile(incoming_text):
                logger.warning(f"🚫 Hostile / opt-out live event from lead {clean_name}: {incoming_text}. Marking opted_out and closing dialogue.")
                self.memory.set_opted_out(user_id_str)
                self.memory.add_message(user_id_str, "user", incoming_text, user_info, message_id=event.message.id)
                farewell = "با نهایت احترام، ارتباط شما از فهرست پیگیری ما خارج شد و پیامی ارسال نخواهد شد. برای شما آرزوی موفقیت و روزگار خوش دارم 🙏"
                await self.client.send_message(sender, farewell, reply_to=event.message.id, link_preview=False, parse_mode='md')
                self.memory.add_message(user_id_str, "model", farewell)
                return

            cust_email = None
            email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', incoming_text)
            if email_match:
                cust_email = email_match.group(0)
            else:
                prev_info = self.memory.memory.get(user_id_str, {}).get("user_info", {})
                if prev_info.get("email"):
                    cust_email = prev_info.get("email")

            lead_ctx = "مشاوره و خدمات هوش مصنوعی وب‌سایت aiabed.ir"
            if cust_email:
                user_info["email"] = cust_email
                if not self.memory.memory.get(user_id_str, {}).get("meet_invite_sent"):
                    schedule_and_send_meet_invite(customer_name=clean_name, customer_email=cust_email, meeting_time=get_default_meeting_time_str())
                    self.memory.memory.setdefault(user_id_str, {})["meet_invite_sent"] = True
                lead_ctx += f" | ایمیل ({cust_email}) ثبت و دعوت‌نامه ارسال شد."

            self.memory.add_message(user_id_str, "user", incoming_text, user_info, message_id=event.message.id)
            await asyncio.sleep(random.uniform(1.5, 3.0))

            history = self.memory.get_history(user_id_str)
            reply = self.brain.generate_reply(history=history, customer_name=clean_name, lead_context=lead_ctx)
            reply = ensure_aiabed_links(reply)

            await self.client.send_message(sender, reply, reply_to=event.message.id, link_preview=False, parse_mode='md')
            self.memory.add_message(user_id_str, "model", reply)
            logger.info(f"📤 Sent live reply to {clean_name}: {reply}")

        # Keep running and check Supabase periodically
        while True:
            await self.poll_supabase_leads()
            await self.poll_website_admin_contacts()
            await asyncio.sleep(120)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["cron", "daemon"], default="cron")
    args = parser.parse_args()

    runner = CloudSalesRunner()
    if args.mode == "daemon":
        asyncio.run(runner.run_daemon())
    else:
        asyncio.run(runner.run_cron())
