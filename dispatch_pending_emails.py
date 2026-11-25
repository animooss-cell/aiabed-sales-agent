import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from google_meet_mailer import schedule_and_send_meet_invite, MEETINGS_FILE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("EmailDispatcher")

def dispatch_all_unsent():
    if not MEETINGS_FILE.exists():
        logger.info("No meetings file found.")
        return

    with open(MEETINGS_FILE, "r", encoding="utf-8") as f:
        meetings = json.load(f)

    unsent_count = 0
    for m in meetings:
        if not m.get("sent_status", False) and m.get("customer_email") and "@" in m.get("customer_email"):
            unsent_count += 1
            logger.info(f"Dispatching invite to {m['customer_name']} ({m['customer_email']})...")
            # attempt send
            schedule_and_send_meet_invite(
                customer_name=m["customer_name"],
                customer_email=m["customer_email"],
                meeting_time=m.get("meeting_time", "یکشنبه ۹ آذر ساعت ۱۷:۰۰"),
                meet_link=m.get("meet_link", "https://meet.google.com/abed-ai-session")
            )

    logger.info(f"Processed {unsent_count} unsent meetings.")

if __name__ == "__main__":
    dispatch_all_unsent()
