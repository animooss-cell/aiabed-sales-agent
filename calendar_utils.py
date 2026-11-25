import datetime
from typing import Dict, Tuple, List

def gregorian_to_jalali(gy: int, gm: int, gd: int) -> Tuple[int, int, int]:
    """Converts a Gregorian date to Jalali (Solar Hijri) mathematically with 100% precision."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy if gm > 2 else gy - 1
    days = 365 * gy + (gy2 + 4) // 4 - (gy2 + 100) // 100 + (gy2 + 400) // 400 - 80 + gd + g_d_m[gm - 1]
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd

WEEKDAYS_FA = {
    0: 'دوشنبه',
    1: 'سه‌شنبه',
    2: 'چهارشنبه',
    3: 'پنج‌شنبه',
    4: 'جمعه',
    5: 'شنبه',
    6: 'یکشنبه'
}

MONTHS_FA = [
    '', 'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
]

def get_optimal_meeting_slots() -> Tuple[str, str]:
    """Calculates optimal meeting slots (1 to 2 days later, between 19:00 and 22:00)."""
    now = datetime.datetime.now()
    d1 = now + datetime.timedelta(days=1)
    d2 = now + datetime.timedelta(days=2)

    jy1, jm1, jd1 = gregorian_to_jalali(d1.year, d1.month, d1.day)
    jy2, jm2, jd2 = gregorian_to_jalali(d2.year, d2.month, d2.day)

    slot1 = f"{WEEKDAYS_FA[d1.weekday()]} {jd1} {MONTHS_FA[jm1]} ساعت ۲۰:۰۰"
    slot2 = f"{WEEKDAYS_FA[d2.weekday()]} {jd2} {MONTHS_FA[jm2]} ساعت ۲۰:۳۰"
    return slot1, slot2

def get_default_meeting_time_str() -> str:
    """Returns the primary recommended meeting slot (2 days later at 20:00)."""
    _, slot2 = get_optimal_meeting_slots()
    return slot2

def get_current_jalali_calendar_context() -> str:
    """Generates an accurate real-time calendar reference for Gemini to prevent date and weekday hallucinations."""
    now = datetime.datetime.now()
    jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
    today_wname = WEEKDAYS_FA[now.weekday()]
    today_str = f"{today_wname} {jd} {MONTHS_FA[jm]} {jy}"

    slot1, slot2 = get_optimal_meeting_slots()

    lines = [
        f"📅 **مرجع دقیق تقویم هجری شمسی و زمان‌بندی طلایی جلسات:**",
        f"- **امروز:** {today_str}",
        f"\n🎯 **استراتژی حیاتی تنظیم زمان جلسه (روانشناسی فروش و کاهش مقاومت مخاطب):**",
        f"۱. **پرهیز از زمان‌های خیلی نزدیک (همان روز):** تنظیم نزدیک‌ترین زمان (مثلاً همان روز) باعث مقاومت مخاطب می‌شود چون یا برنامه‌ریزی قبلی دارد یا آمادگی ذهنی ندارد.",
        f"۲. **پرهیز از زمان‌های دور (هفته بعد):** تعیین زمان خیلی دور باعث سرد شدن سرنخ فروش می‌شود.",
        f"۳. **پنجره طلایی استاندارد:** بهترین زمان برگزاری جلسه **دقیقاً ۱ الی ۲ روز بعد از مکالمه**، در ساعات عصر/شب و **بین ساعت ۱۹:۰۰ تا ۲۲:۰۰** است (مثلاً ساعت ۲۰:۰۰ یا ۲۰:۳۰).",
        f"۴. **دو گزینه پیشنهادی آماده برای شما جهت ارائه به مخاطب:**",
        f"   - گزینه اول (فردا): «{slot1}»",
        f"   - گزینه دوم (پس‌فردا): «{slot2}»",
        f"\n📌 **تقویم ۷ روز آینده جهت ارجاع دقیق:**"
    ]

    for i in range(1, 8):
        fut = now + datetime.timedelta(days=i)
        fjy, fjm, fjd = gregorian_to_jalali(fut.year, fut.month, fut.day)
        fwname = WEEKDAYS_FA[fut.weekday()]
        if i == 1:
            rel = "فردا"
        elif i == 2:
            rel = "پس‌فردا"
        else:
            rel = f"{i} روز بعد"
        lines.append(f"- **{rel}:** {fwname} {fjd} {MONTHS_FA[fjm]} {fjy}")

    return "\n".join(lines)
