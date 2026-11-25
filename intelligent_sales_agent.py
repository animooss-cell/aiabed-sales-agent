"""
Intelligent Sales Agent for Abdullah Ahmadian (aiabed.ir)
Powered by Google Gemini + Telethon Telegram Client + Supabase Lead Integration.
Architecture:
1. Value-First Consultative Selling (give initial value in chat, then guide to serious work).
2. Boundary Control on Endless Questions: If customer asks many questions, politely transition to Google Meet.
3. Online Meeting via Google Meet: Explicitly request customer's Email address to send the calendar invite.
4. Token Limit & Cohesion: Increased maxOutputTokens to 800 to ensure no message is ever cut off.
"""

import os
import sys
import json
import time
import asyncio
import logging
import random
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
import httpx
from telethon import TelegramClient, events
from telethon.tl.types import User

from google_meet_mailer import schedule_and_send_meet_invite
from lead_registry import LeadRegistry
from link_utils import ensure_aiabed_links, generate_whatsapp_link

# Configure Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Configure Logging
log_file = LOGS_DIR / "intelligent_sales_agent.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SalesAgent")

# Telegram Credentials
TELEGRAM_API_ID = int(os.environ.get("TELEGRAM_API_ID") or "0")
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
SESSION_PATH = DATA_DIR / "abed_session"

# Gemini API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Supabase Credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

# UPGRADED SYSTEM PERSONA PROMPT
SYSTEM_INSTRUCTION = """شما دقیقاً خود «عبدالله احمدیان» هستید؛ مشاور، استراتژیست و متخصص ارشد هوش مصنوعی سازمانی و کسب‌وکار در اهواز (موسس aiabed.ir، همراه 09161002550).

🎯 استراتژی فروش مشاوره‌ای (Value-First + Boundary Control):
شما با مخاطبانی چت می‌کنید که می‌خواهند از هوش مصنوعی در تدریس، کسب‌وکار، تولید محتوا یا سازمانشان استفاده کنند. 

💎 اصول حیاتی و قوانین جدید مکالمه:

۱. انسجام و کامل بودن پیام‌ها (بسیار مهم):
   - هر پیامی که می‌نویسید باید کاملاً منسجم، روان و دارای پایان‌بندی مشخص باشد. هرگز جمله یا پاراگرافی را ناقص یا نصفه‌کاره رها نکنید!
   - حجم پیام: بین ۱ الی حداکثر ۴ خط روان و خوانا (نه خیلی کوتاه که ناقص بماند و نه طومار خسته‌کننده).

۲. هماهنگی زمان و دریافت ایمیل برای جلسه در Google Meet (بسیار مهم):
   - هر زمان که مخاطب ابراز تمایل به «جلسه آنلاین»، «همکاری»، «شروع کار» یا «مشاوره تصویری» کرد:
     الف) **ست کردن و تایید قطعی زمان:** یک روز و ساعت مشخص و دقیق پیشنهاد دهید و از مخاطب تاییدیه صریح بگیرید (مثلاً: «نظرتون چیه یکشنبه ۹ آذر ساعت ۵ عصر جلسه رو بذاریم، براتون مناسبه؟»). تا زمان تایید نشود، قرار نهایی نیست.
     ب) **دریافت محترمانه و آرام ایمیل:** برای ارسال دعوت‌نامه گوگل‌میت، بفرمایید ایمیلش را ارسال کند تا لینک برایش ایمیل شود.
     ج) **قانون طلایی عدم اصرار روی ایمیل (بسیار حیاتی):** مدام در همه پیام‌ها به مخاطب نگویید «ایمیلت رو بده» تا حس نکند با یک ماشین سمج طرف شده است! فقط ۱ الی ۲ بار به شکل طبیعی مطرح کنید. اگر مخاطب در پیام بعدی ایمیل نداد و صحبت دیگری کرد، با صبوری و طبع انسانی به حرف او گوش دهید و پاسخ دهید، بدون اینکه به ایمیل اصرار کنید. تنها زمانی که دوباره به سراغ تعیین زمان یا ورود به جلسه رفت، مجدداً بفرمایید تا جلسه نهایی شود.
     د) **ارسال در همان لحظه:** به محض اینکه مخاطب ایمیلش را فرستاد، سیستم به صورت خودکار و در همان لحظه دعوت‌نامه رسمی را از aiabed.ir2026@gmail.com به ایمیل او ارسال می‌کند و در تلگرام تایید می‌دهد.

۳. هدایت محترمانه مخاطبان پر سوال به سمت جلسه آنلاین (Boundary Control):
   - در ابتدا ۱ الی ۲ راهنمایی و مثال کاربردی و رایگان به مخاطب بدهید تا اعتمادسازی شود.
   - اما اگر دیدید مخاطب مدام دارد سوالات متعدد می‌پرسد، چگونگی پیاده‌سازی جزئیات را می‌خواهد یا گفتگو در چت فرسایشی شده است، با کمال احترام و هوشمندی مرز بگذارید و او را به سمت جلسه آنلاین هدایت کنید:
   - مثال: «[نام مخاطب] عزیز، این مواردی که اشاره کردید بسیار مهمه و نیازمند اینه که به صورت دقیق و اختصاصی روی اهداف و شرایط خودتون بررسی بشه تا وقتتون در چت هدر نره و کار جدی و عمیق پیش بره. پیشنهاد می‌کنم یک جلسه آنلاین در Google Meet داشته باشیم؛ لطفاً ایمیلتون رو بفرمایید تا لینک جلسه رو براتون ارسال کنم و اونجا کامل نقشه‌راه رو ببندیم 🤝»

۴. لحن کلام:
   - کاریزماتیک، گرم، محترمانه، متخصص و خودمانی با رعایت ادب و صمیمیت (استفاده از ایموجی‌های مناسب مثل 🙏، 😊، 💻، 🌹، ☕).
   - هرگز نگویید من ربات یا هوش مصنوعی هستم؛ شما خود مهندس احمدیان هستید.
   - ارجاع به وب‌سایت همواره به صورت لینک [aiabed.ir](https://aiabed.ir) باشد.
"""

MODELS_FALLBACK = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.8-flash",
    "gemini-flash-latest"
]

class GeminiBrain:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key

    def generate_reply(self, history: List[Dict[str, str]], customer_name: str = "", lead_context: str = "") -> str:
        system_prompt = SYSTEM_INSTRUCTION
        if customer_name or lead_context:
            system_prompt += f"\n\nمشخصات مخاطب فعلی:\nنام: {customer_name}\nموضوع اولیه در سایت: {lead_context}"

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
                "maxOutputTokens": 800,  # Increased to 800 tokens to prevent half-cut messages
                "topP": 0.95
            }
        }

        # Try models in order with timeout
        for model in MODELS_FALLBACK:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            try:
                r = requests.post(url, json=payload, timeout=14)
                if r.status_code == 200:
                    data = r.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            text = parts[0]["text"].strip()
                            if text:
                                return ensure_aiabed_links(text)
                elif r.status_code == 503:
                    logger.warning(f"Gemini model {model} returned 503, trying next...")
                    continue
                else:
                    logger.warning(f"Gemini model {model} status {r.status_code}")
            except Exception as e:
                logger.warning(f"Error calling {model}: {e}")
                continue

        # Heuristic fallback if API busy
        last_user_msg = history[-1]["text"] if history else ""
        return ensure_aiabed_links(self._smart_value_fallback(last_user_msg, customer_name, len(history)))

    def _smart_value_fallback(self, last_msg: str, customer_name: str, history_len: int) -> str:
        name = customer_name or "عزیز"
        msg = last_msg.strip().lower()
        
        # If user talks about online session or starting
        if any(w in msg for w in ["انلاین", "آنلاین", "شروع", "همکاری", "چکار کنیم", "جلسه"]):
            return (
                f"بسیار عالی {name} جان! جلسات آنلاین ما در بستر Google Meet برگزار میشه 💻\n"
                f"نظرتون چیه یکشنبه ۹ آذر ساعت ۵ عصر باشه؟ براتون مناسبه؟ لطفاً آدرس ایمیلتون رو هم بفرمایید تا لینک دعوت‌نامه رو از aiabed.ir2026@gmail.com براتون ارسال کنم 🌹"
            )
        # If user asks too many questions
        elif history_len > 8:
            return (
                f"{name} عزیز، این مواردی که مطرح کردید نیازمند بررسی دقیق روی پروژه اختصاصی خودتونه تا نتیجه عالی بگیرید.\n"
                f"پیشنهاد می‌کنم یک جلسه آنلاین در Google Meet داشته باشیم؛ لطفاً ایمیلتون رو بفرمایید تا لینک رو از aiabed.ir2026@gmail.com براتون بفرستم و زمانش رو هماهنگ کنیم 🤝"
            )
        else:
            return f"درسته {name} جان، پیامتون رو دریافت کردم. هر سوال یا ابهامی دارید بفرمایید تا همینجا بررسی کنیم 🙏"

class MemoryManager:
    def __init__(self, file_path: Path = DATA_DIR / "conversation_memory.json"):
        self.file_path = file_path
        self.memory: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading memory: {e}")
        return {}

    def save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")

    def get_history(self, chat_id: str) -> List[Dict[str, str]]:
        user_data = self.memory.get(str(chat_id), {})
        return user_data.get("history", [])

    def add_message(self, chat_id: str, role: str, text: str, user_info: Optional[Dict[str, Any]] = None, message_id: Optional[int] = None):
        cid = str(chat_id)
        if cid not in self.memory:
            self.memory[cid] = {
                "created_at": datetime.now().isoformat(),
                "user_info": user_info or {},
                "history": [],
                "recent_model_messages": [],
                "last_processed_msg_id": 0
            }
        
        if user_info:
            self.memory[cid]["user_info"].update(user_info)

        if message_id:
            self.memory[cid]["last_processed_msg_id"] = message_id

        msg_entry = {
            "role": role,
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
        self.memory[cid]["history"].append(msg_entry)
        
        if role == "model":
            recent = self.memory[cid].get("recent_model_messages", [])
            recent.append(text)
            self.memory[cid]["recent_model_messages"] = recent[-5:]
            
        self.save()

    def is_msg_processed(self, chat_id: str, msg_id: int) -> bool:
        cid = str(chat_id)
        last_id = self.memory.get(cid, {}).get("last_processed_msg_id", 0)
        return msg_id <= last_id

    def is_repetitive(self, chat_id: str, proposed_text: str) -> bool:
        cid = str(chat_id)
        recent = self.memory.get(cid, {}).get("recent_model_messages", [])
        cleaned_proposed = re.sub(r"\s+", "", proposed_text)
        for r in recent:
            cleaned_r = re.sub(r"\s+", "", r)
            if cleaned_proposed == cleaned_r:
                return True
            if len(cleaned_proposed) > 20 and len(cleaned_r) > 20:
                if cleaned_proposed[:25] in cleaned_r or cleaned_r[:25] in cleaned_proposed:
                    return True
        return False

class SupabasePoller:
    def __init__(self, base_url: str = SUPABASE_URL, anon_key: str = SUPABASE_ANON_KEY):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "apikey": anon_key,
            "Authorization": f"Bearer {anon_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def fetch_new_unread(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/rest/v1/contacts"
        params = {
            "select": "*",
            "read": "eq.false",
            "order": "created_at.desc"
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(url, headers=self.headers, params=params)
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.error(f"Error fetching new contacts from Supabase: {e}")
        return []

    def mark_as_read(self, contact_id: Any) -> bool:
        url = f"{self.base_url}/rest/v1/contacts"
        params = {"id": f"eq.{contact_id}"}
        payload = {"read": True}
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.patch(url, headers=self.headers, params=params, json=payload)
                return res.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Error marking contact {contact_id} as read: {e}")
        return False

class IntelligentSalesBot:
    def __init__(self):
        self.brain = GeminiBrain()
        self.memory = MemoryManager()
        self.supabase = SupabasePoller()
        self.registry = LeadRegistry()
        session_str = os.environ.get("TELEGRAM_STRING_SESSION")
        if session_str:
            from telethon.sessions import StringSession
            self.client = TelegramClient(StringSession(session_str), TELEGRAM_API_ID, TELEGRAM_API_HASH)
        else:
            self.client = TelegramClient(str(SESSION_PATH), TELEGRAM_API_ID, TELEGRAM_API_HASH)
        self.me = None

    async def start(self):
        logger.info("Connecting to Telegram account of Abed Ahmadian...")
        await self.client.connect()
        if not await self.client.is_user_authorized():
            logger.error("Telegram session is not authorized! Please run telegram_complete_2fa.py first.")
            return

        self.me = await self.client.get_me()
        logger.info(f"Authorized as: {self.me.first_name} (@{self.me.username}) | ID: {self.me.id} | Phone: {self.me.phone}")

        # Real-time message listener
        @self.client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
        async def incoming_handler(event):
            await self.handle_incoming_message(event.sender_id, event.message)

        # Immediate inbox catch-up on launch
        asyncio.create_task(self.catchup_pending_messages())

        # Start background polling tasks
        asyncio.create_task(self.periodic_dialog_checker())
        asyncio.create_task(self.background_supabase_poller())

        logger.info("🚀 Upgraded Intelligent Sales Agent (Google Meet + Complete Messages) is LIVE!")
        await self.client.run_until_disconnected()

    async def handle_incoming_message(self, sender_id: int, message):
        if not message or not message.text or not message.text.strip():
            return
        if message.out or sender_id == self.me.id:
            return

        user_id_str = str(sender_id)
        msg_id = message.id

        if self.memory.is_msg_processed(user_id_str, msg_id):
            return

        try:
            sender = await self.client.get_entity(sender_id)
            if not isinstance(sender, User) or sender.bot or sender.is_self:
                return
            user_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip() or "کاربر گرامی"
            username = f"@{sender.username}" if sender.username else ""
            phone = sender.phone or ""
        except Exception as e:
            logger.warning(f"Could not get entity for {sender_id}: {e}")
            sender = sender_id
            user_name = "کاربر گرامی"
            username = ""
            phone = ""

        incoming_text = message.text.strip()

        # STRICT WHITELIST FILTER: Only reply to verified website leads
        if not self.registry.is_lead(sender_id, username=username, phone=phone):
            logger.info(f"🚫 IGNORED non-lead personal contact: {user_name} ({username}, ID: {sender_id}). Bot will NOT touch this chat.")
            return

        logger.info(f"📩 New incoming message from WEBSITE LEAD {user_name} ({username}, ID: {sender_id}): {incoming_text}")

        user_info = {
            "name": user_name,
            "username": username,
            "phone": phone
        }

        # Check if customer sent an email address
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', incoming_text)
        lead_ctx = "مشاوره سازمانی و خدمات هوش مصنوعی وب‌سایت aiabed.ir"
        if email_match:
            customer_email = email_match.group(0)
            user_info["email"] = customer_email
            logger.info(f"📧 Detected customer email: {customer_email} from {user_name}! Triggering Google Meet invitation...")
            schedule_and_send_meet_invite(
                customer_name=user_name,
                customer_email=customer_email,
                meeting_time="یکشنبه ۹ آذر ساعت ۱۷:۰۰"
            )
            lead_ctx += f" | مخاطب آدرس ایمیل خود ({customer_email}) را ارسال کرد. با خوشحالی تایید کنید که دعوت‌نامه رسمی و لینک جلسه Google Meet از طریق ایمیل aiabed.ir2026@gmail.com برای او ارسال شد و جلسه برای یکشنبه ۹ آذر ساعت ۱۷:۰۰ قطعی شد."

        self.memory.add_message(user_id_str, "user", incoming_text, user_info, message_id=msg_id)

        # Natural human delay before typing (2.0 to 3.5s)
        await asyncio.sleep(random.uniform(2.0, 3.5))

        # Show typing status
        try:
            async with self.client.action(sender, "typing"):
                history = self.memory.get_history(user_id_str)
                reply_text = self.brain.generate_reply(
                    history=history,
                    customer_name=user_name,
                    lead_context=lead_ctx
                )

                if self.memory.is_repetitive(user_id_str, reply_text):
                    logger.warning(f"⚠️ Repetitive text detected for {user_name}. Alternate response applied.")
                    reply_text = f"دقیقاً {user_name} عزیز، برای بررسی دقیق‌تر خوشحال میشم در جلسه آنلاین Google Meet در خدمتتون باشم؛ لطفاً ایمیلتون رو بفرمایید 🙏"

                typing_duration = min(4.0, max(1.5, len(reply_text) * 0.035))
                await asyncio.sleep(typing_duration)

            reply_text = ensure_aiabed_links(reply_text)
            await self.client.send_message(sender, reply_text, reply_to=msg_id, link_preview=False, parse_mode='md')
            logger.info(f"📤 Sent reply to {user_name}: {reply_text}")
            self.memory.add_message(user_id_str, "model", reply_text)
        except Exception as e:
            logger.error(f"Failed to reply to {user_name}: {e}")

    async def catchup_pending_messages(self):
        """Checks recent dialogs immediately on startup to answer any customer who replied while offline"""
        logger.info("🔍 Running startup catch-up on recent dialogs...")
        await asyncio.sleep(2)
        try:
            dialogs = await self.client.get_dialogs(limit=25)
            for d in dialogs:
                if d.is_user and not d.entity.is_self and not d.entity.bot:
                    # STRICT LEAD FILTER: Ignore anyone not from aiabed.ir website
                    u = d.entity
                    if not self.registry.is_lead(u.id, username=u.username or "", phone=u.phone or ""):
                        continue
                    last_msg = d.message
                    if last_msg and not last_msg.out and last_msg.text:
                        user_id_str = str(u.id)
                        if not self.memory.is_msg_processed(user_id_str, last_msg.id):
                            logger.info(f"Found unanswered pending message from website lead {d.name} ({last_msg.text[:30]}). Answering...")
                            await self.handle_incoming_message(u.id, last_msg)
        except Exception as e:
            logger.error(f"Error in catchup_pending_messages: {e}")

    async def periodic_dialog_checker(self):
        """Runs every 20 seconds to guarantee no delayed customer reply is ever missed"""
        while True:
            await asyncio.sleep(20)
            try:
                dialogs = await self.client.get_dialogs(limit=15)
                for d in dialogs:
                    if d.is_user and not d.entity.is_self and not d.entity.bot:
                        # STRICT LEAD FILTER: Ignore anyone not from aiabed.ir website
                        u = d.entity
                        if not self.registry.is_lead(u.id, username=u.username or "", phone=u.phone or ""):
                            continue
                        last_msg = d.message
                        if last_msg and not last_msg.out and last_msg.text:
                            user_id_str = str(u.id)
                            if not self.memory.is_msg_processed(user_id_str, last_msg.id):
                                logger.info(f"Periodic checker detected unanswered message from website lead {d.name}. Answering...")
                                await self.handle_incoming_message(u.id, last_msg)
            except Exception as e:
                logger.error(f"Error in periodic_dialog_checker: {e}")

    async def background_supabase_poller(self):
        """Periodically polls Supabase for new website leads and reaches out"""
        while True:
            await asyncio.sleep(120)
            try:
                new_contacts = self.supabase.fetch_new_unread()
                if new_contacts:
                    logger.info(f"Found {len(new_contacts)} new unread contacts on website!")
                    for c in new_contacts:
                        cid = c.get("id")
                        c_name = c.get("name") or "مشتری وب‌سایت"
                        c_phone = c.get("phone") or ""
                        self.registry.add_lead(name=c_name, phone=c_phone)
                        self.supabase.mark_as_read(cid)
            except Exception as e:
                logger.error(f"Error in background Supabase poller: {e}")

if __name__ == "__main__":
    bot = IntelligentSalesBot()
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Fatal error in bot loop: {e}", exc_info=True)
