import os
import time
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import httpx

from config import DATA_DIR, LOGS_DIR

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SalesAgent.Bot")

# تاریخچه مکالمات برای هر کاربر
CONVERSATIONS_FILE = DATA_DIR / "conversations_history.json"

SYSTEM_PROMPT = """شما «ایجنت هوشمند و دستیار ارشد فروش عبدالله احمدیان» هستید (یا در نقش خود عبدالله احمدیان به صورت صمیمی، حرفه‌ای و فوق‌العاده باهوش صحبت می‌کنید).
اطلاعات کلیدی شما:
- هویت: عبدالله احمدیان، مشاور و مدرس ارشد هوش مصنوعی سازمانی و کسب‌وکار در اهواز، خوزستان و سراسر کشور.
- سوابق: بیش از ۱۰ سال سابقه، مدرس فولاد خوزستان، فولاد اکسین و ده‌ها شرکت صنعتی و بازرگانی.
- خدمات کلیدی:
  ۱) مشاوره هوش مصنوعی کسب‌وکار (عارضه‌یابی و پیدا کردن نقاطی که AI هزینه و زمان را کم می‌کند)
  ۲) دوره جامع مسئول دفتر هوشمند با AI (۱۶ ساعت - کار با مکاتبات رسمی، گزارش‌ها، هوش مصنوعی در Excel و اسلایدسازی)
  ۳) آموزش تولید محتوا و رشد پیج اینستاگرام و یوتیوب با هوش مصنوعی
  ۴) مشاوره رشد استارتاپ و کسب‌وکار
- سیاست قیمت‌گذاری: جلسه اول ارزیابی و مشاوره (۴۵ دقیقه - آنلاین یا حضوری در اهواز) کاملاً رایگان است. پس از مشخص شدن نیاز دقیق، پیش‌فاکتور و پروپوزال شفاف مکتوب ارائه می‌شود.
- اطلاعات تماس: تلفن و واتساپ: 09161002550 | تلگرام شخصی: @abedahm | سایت: aiabed.ir

دستورالعمل لحن و مذاکره (Humanized Sales):
۱) کاملاً لحن گرم، انسانی، صمیمی، مطمئن و نتیجه‌گرا داشته باشید.
۲) هرگز پاسخ‌های طولانی، خسته‌کننده یا شبیه متن کاتالوگ ندهید؛ پاسخ‌ها کوتاه (۲ تا ۴ بند کوتاه)، پرانرژی و متناسب با چت تلگرام باشند.
۳) به هر سوالی که مشتری درباره دوره، سرفصل‌ها، حضوری یا آنلاین بودن و ... بپرسد، کامل و با اعتماد به نفس پاسخ دهید.
۴) هدف نهایی هر پیام: گرفتن تایید مشتری برای ثبت تایم جلسه اول رایگان ۴۵ دقیقه‌ای (آنلاین یا حضوری در اهواز) یا تماس تلفنی.
"""

def load_history() -> Dict[str, List[Dict[str, str]]]:
    if CONVERSATIONS_FILE.exists():
        try:
            with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_history(history: Dict[str, List[Dict[str, str]]]):
    with open(CONVERSATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def generate_human_reply(user_id: str, user_name: str, incoming_text: str) -> str:
    """
    تولید پاسخ هوشمند و انسان‌گونه با هوش مصنوعی یا قوانین فروش حرفه‌ای
    """
    # پاسخ‌های هوشمند برای سناریوهای رایج
    t = incoming_text.lower()

    if any(k in t for k in ["سلام", "درود", "وقت بخیر", "start", "/start"]):
        return (
            f"سلام {user_name} عزیز، وقتتون بخیر 🎯\n"
            f"من عبدالله احمدیان هستم (مشاور و مدرس هوش مصنوعی). خوشحالم باهم در ارتباطیم.\n\n"
            f"بفرمایید در چه حوزه‌ای (مشاوره کسب‌وکار، آموزش‌های هوش مصنوعی سازمانی، یا تولید محتوا) می‌تونم کمکتون کنم تا دقیق راهنماییتون کنم؟"
        )

    if any(k in t for k in ["قیمت", "هزینه", "شهریه", "چنده"]):
        return (
            f"در مورد هزینه‌ها کاملاً خیالتون راحت باشه؛ ما جلسه اول ارزیابی و نیازسنجی (۴۵ دقیقه - آنلاین یا حضوری در اهواز) رو کاملاً **رایگان** برگزار می‌کنیم 💡\n\n"
            f"توی این جلسه دقیقاً بررسی می‌کنیم نیاز شما چیه و بعد یک پیشنهاد شفاف با کمترین هزینه و بیشترین بازدهی براتون تنظیم می‌کنیم.\n"
            f"چه روزی براتون مناسب‌تره تا تایم جلسه رایگان رو فیکس کنیم؟"
        )

    if any(k in t for k in ["مسئول دفتر", "اداری", "اکسل", "نامه"]):
        return (
            f"دوره «مسئول دفتر هوشمند با هوش مصنوعی» دقیقاً برای همین هدف طراحی شده 🎓\n"
            f"• ۱۶ ساعت آموزش کاملاً عملیاتی\n"
            f"• تمرین روی نامه‌های اداری واقعی، فرمول‌های هوشمند اکسل و خلاصه‌سازی گزارش‌های سنگین با AI\n"
            f"• برگزاری آنلاین و حضوری همراه با گواهی معتبر\n\n"
            f"برای هماهنگی سرفصل‌ها و زمان برگزاری، تمایل دارید یک تماس تلفنی کوتاه داشته باشیم یا در جلسه آنلاین رایگان بررسی کنیم؟"
        )

    if any(k in t for k in ["اینستا", "پیج", "محتوا", "فروش", "یوتیوب", "میکاپ"]):
        return (
            f"در حوزه رشد پیج و تولید محتوا، ما به جای تولید محتوای تزئینی، یک «قیف فروش هوشمند» طراحی می‌کنیم 🚀\n"
            f"از سناریونویسی وایرال تا ادیت سریع ویدیو با هوش مصنوعی که منجر به فروش واقعی بشه.\n\n"
            f"پیشنهاد می‌کنم یک جلسه رایگان ۴۵ دقیقه‌ای بگذاریم تا پیج یا کسب‌وکارتون رو عارضه‌یابی کنیم. موافقید؟"
        )

    # پاسخ عمومی همگرا به سمت بستن قرارداد
    return (
        f"دقیقاً نکته مهمی رو مطرح کردید {user_name} جان 💼\n"
        f"برای اینکه بهترین نتیجه رو بگیرید و وقت و هزینه‌تون هدر نره، پیشنهاد می‌کنم یک گفتگوی ۴۵ دقیقه‌ای رایگان (آنلاین یا تلفنی) داشته باشیم تا دقیق‌ترین راهکار رو بهتون بگم.\n\n"
        f"اگر موافقید شماره تماستون یا زمان پیشنهادی‌تون رو بفرمایید تا ثبتش کنم."
    )

def send_telegram_message(chat_id: int, text: str):
    """
    ارسال پیام با شبیه‌سازی وضعیت Typing مثل انسان
    """
    try:
        with httpx.Client(timeout=15.0) as client:
            # ارسال وضعیت "در حال تایپ..."
            client.post(f"{TELEGRAM_API_URL}/sendChatAction", json={"chat_id": chat_id, "action": "typing"})
            time.sleep(2.5)  # تاخیر طبیعی ۲.۵ ثانیه‌ای
            # ارسال پیام اصلی
            client.post(f"{TELEGRAM_API_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            })
    except Exception as e:
        logger.error(f"خطا در ارسال پیام تلگرام: {e}")

def run_bot_listener():
    """
    شنود پیام‌های دریافتی تلگرام به صورت Long Polling ۲۴ ساعته
    """
    logger.info("🤖 ربات تلگرام فروش فعال شد (@aiabedsales_bot). آماده دریافت پیام‌های مخاطبان...")
    offset = 0

    while True:
        try:
            with httpx.Client(timeout=40.0) as client:
                res = client.get(f"{TELEGRAM_API_URL}/getUpdates", params={"offset": offset, "timeout": 30})
                if res.status_code == 200:
                    data = res.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        msg = update.get("message")
                        if not msg or "text" not in msg:
                            continue

                        chat_id = msg["chat"]["id"]
                        first_name = msg["from"].get("first_name", "کاربر")
                        user_text = msg["text"]

                        logger.info(f"📩 پیام جدید از {first_name} ({chat_id}): {user_text}")

                        # تولید پاسخ انسانی و هوشمند
                        reply_text = generate_human_reply(str(chat_id), first_name, user_text)

                        # ارسال با شبیه‌سازی تایپ
                        send_telegram_message(chat_id, reply_text)
                        logger.info(f"✅ پاسخ با موفقیت به {first_name} ارسال شد.")
                else:
                    logger.warning(f"کد پاسخ تلگرام: {res.status_code}")
                    time.sleep(3)
        except Exception as e:
            logger.error(f"خطا در حلقه ربات تلگرام: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot_listener()
