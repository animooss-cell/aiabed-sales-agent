import sys
import json
from pathlib import Path
from agent import DailySalesAgent
from config import PHONE_LEADS_FILE

def main():
    agent = DailySalesAgent()
    print("=" * 60)
    print("🤖 ایجنت فروش هوشمند aiabed.ir — بررسی پیام‌های «تماس با ما»")
    print("=" * 60)
    print("1. بررسی و پیش‌نمایش پیام‌های جدید «تماس با ما» (بدون باز شدن مرورگر)")
    print("2. بررسی و ارسال فوری در واتساپ وب (باز شدن خودکار تب چت)")
    print("3. مشاهده لیست مخاطبانی که باید با آن‌ها تماس تلفنی بگیرید")
    print("4. اجرای زمان‌بندی خودکار روزانه (هر روز راس ساعت ۱۰:۰۰)")
    print("=" * 60)

    choice = input("لطفاً یک گزینه را انتخاب کنید (1/2/3/4): ").strip()

    if choice == "1":
        results = agent.process_new_contacts(auto_open_whatsapp=False)
        if results:
            print(f"\n✅ تعداد {len(results)} پیام آماده شد:")
            for idx, r in enumerate(results, 1):
                print(f"\n[{idx}] {r['name']} ({r['phone']}) - کانال: {r['channel']}")
                print(f"وضعیت: {r['action']}")
                print(f"متن پیام:\n{r['draft']}")
                print("-" * 40)
        else:
            print("\nپیام جدید خوانده‌نشده‌ای یافت نشد.")

    elif choice == "2":
        print("\nدر حال پردازش و باز کردن گفتگوی واتساپ وب برای پیام‌ها...")
        agent.process_new_contacts(auto_open_whatsapp=True)

    elif choice == "3":
        if PHONE_LEADS_FILE.exists():
            with open(PHONE_LEADS_FILE, "r", encoding="utf-8") as f:
                leads = json.load(f)
            print(f"\n📞 لیست تماس‌های تلفنی نیازمند پیگیری شما ({len(leads)} نفر):")
            for idx, l in enumerate(leads, 1):
                print(f"\n{idx}. نام: {l.get('name')} | شماره: {l.get('phone')}")
                print(f"   کسب‌وکار: {l.get('business')}")
                print(f"   متن پیام مشتری: {l.get('message')}")
                print(f"   پیشنهاد مطرح‌شدنی در تماس: {l.get('notes_for_call')[:120]}...")
        else:
            print("\nهنوز مخاطبی برای تماس تلفنی ثبت نشده است.")

    elif choice == "4":
        t = input("ساعت اجرای روزانه را وارد کنید (پیش‌فرض 10:00): ").strip() or "10:00"
        agent.run_daily_scheduler(run_time=t)

    else:
        print("گزینه نامعتبر است.")

if __name__ == "__main__":
    main()
