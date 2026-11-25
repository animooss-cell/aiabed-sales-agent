import os
import time
import json
import logging
import re
import httpx
from typing import List, Dict, Any
from calendar_utils import get_current_jalali_calendar_context
from link_utils import ensure_aiabed_links, sanitize_customer_name

logger = logging.getLogger("GeminiBrain")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

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

CANDIDATE_MODELS = [
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-pro-latest"
]

class GeminiBrain:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key
        self.client = httpx.Client(timeout=35.0)

    def generate_reply(self, history: List[Dict[str, str]], customer_name: str = "", lead_context: str = "") -> str:
        clean_name = sanitize_customer_name(customer_name)
        system_prompt = SYSTEM_INSTRUCTION

        # Inject Real-Time Jalali Calendar Reference
        calendar_ctx = get_current_jalali_calendar_context()
        system_prompt += f"\n\n{calendar_ctx}"

        # Detect previous email in history
        detected_email = None
        for item in history:
            txt = item.get("text", "")
            m = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', txt)
            if m:
                detected_email = m.group(0)

        if detected_email:
            system_prompt += f"\n\n💡 توجه حیاتی: مخاطب قبلاً ایمیل خود ({detected_email}) را ارسال کرده است. به هیچ عنوان دوباره ایمیل درخواست نکنید؛ بلکه تایید کنید که لینک به همین ایمیل ارسال می‌شود/شده است."

        if clean_name or lead_context:
            system_prompt += f"\n\nاطلاعات لید فعلی:\nنام مخاطب: {clean_name}\nزمینه درخواست در سایت: {lead_context}"

        # Dynamic Dialogue Guard: Prevent Broken Record Meeting Proposals
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

        # Dynamic Dialogue Guard: Concrete Samples Directive
        last_user_msg = history[-1]["text"] if history and history[-1]["role"] == "user" else ""
        if any(w in last_user_msg for w in ["نمونه", "مثال", "چطور کار میکنه", "چیکار میشه کرد", "چه کارهایی"]):
            system_prompt += "\n\n💎 دستور حیاتی برای این پیام: مخاطب صریحاً درخواست نمونه یا مثال کرده است. بلافاصله و با دست‌ودلبازی ۱ الی ۲ مثال ملموس، جذاب و واقعی از نحوه پیاده‌سازی هوش مصنوعی با ذکر ابزارهای مشخص (مثل Midjourney، Ideogram، ChatGPT و...) بیان کنید. به هیچ وجه ارائه نمونه را مشروط به جلسه نکنید!"

        # Build contents structure for Gemini REST API
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
                "temperature": 0.75,
                "maxOutputTokens": 600,
                "topP": 0.95
            }
        }

        # Try models in order
        for model in CANDIDATE_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            try:
                resp = self.client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            text = parts[0]["text"].strip()
                            return ensure_aiabed_links(text)
                elif resp.status_code in (429, 503):
                    logger.warning(f"Model {model} returned {resp.status_code}, trying next...")
                    time.sleep(1)
                    continue
                else:
                    logger.error(f"Model {model} returned {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                logger.error(f"Error querying {model}: {e}")
                continue

        # Intelligent Persian fallback if network fails
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

if __name__ == "__main__":
    brain = GeminiBrain()
    sample_history = [
        {"role": "user", "text": "سلام پیامتون در سایت aiabed.ir رو دیدم"},
        {"role": "model", "text": "سلام رقیه خانم عزیز وقتتون بخیر، احمدیان هستم. پیامتون در مورد تولید محتوای مناسبتی رو بررسی کردم."},
        {"role": "user", "text": "وا روز ۹ آذر"},
        {"role": "model", "text": "عالیه پس ۹ آذر رو فیکس کردم براتون. چه ساعتی راحت‌ترید؟ ۵ عصر خوبه؟"},
        {"role": "user", "text": "اره ۵ عصر خوبه، آنلاینه یا حضوری؟"}
    ]
    reply = brain.generate_reply(sample_history, customer_name="رقیه", lead_context="تولید محتوا و ایده مناسبتی")
    print("Brain reply:")
    print(reply)
