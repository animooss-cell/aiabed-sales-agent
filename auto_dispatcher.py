import time
import logging
from datetime import datetime
from agent import DailySalesAgent

logger = logging.getLogger("SalesAgent.AutoDispatcher")

def run_continuous_monitor(interval_seconds: int = 120):
    """
    بررسی مداوم و خودکار سایت aiabed.ir هر ۲ دقیقه
    به محض آمدن پیام جدید، اقدام متناسب را اجرا می‌کند.
    """
    logger.info(f"🚀 مانیتورینگ خودکار پیام‌های جدید فعال شد (هر {interval_seconds} ثانیه)...")
    agent = DailySalesAgent()

    while True:
        try:
            logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] بررسی پیام‌های جدید...")
            agent.process_new_contacts(auto_open_whatsapp=True)
        except Exception as e:
            logger.error(f"خطا در بررسی دوره‌ای: {e}")

        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_continuous_monitor(120)
