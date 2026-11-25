"""
Website Lead Whitelist Registry for aiabed.ir
Strictly limits AI auto-replies ONLY to contacts who originated from the website.
Personal friends, family, coworkers, and non-lead chats are 100% ignored.
"""

import json
import logging
import re
from pathlib import Path
from typing import Set, Dict, Any, Optional

logger = logging.getLogger("LeadRegistry")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
WHITELIST_FILE = DATA_DIR / "website_leads_whitelist.json"

# Loaded dynamically from encrypted vault -> data/website_leads_whitelist.json
INITIAL_LEADS = []

def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    digits = re.sub(r"[^0-9]", "", str(phone))
    if digits.startswith("98"):
        digits = "0" + digits[2:]
    elif not digits.startswith("0") and len(digits) == 10:
        digits = "0" + digits
    return digits

def normalize_username(username: str) -> str:
    if not username:
        return ""
    return username.lstrip("@").strip().lower()

class LeadRegistry:
    def __init__(self, filepath: Path = WHITELIST_FILE):
        self.filepath = filepath
        self.leads = self._load()

    def _load(self) -> Dict[str, Any]:
        DATA_DIR.mkdir(exist_ok=True)
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading whitelist: {e}")
        
        # Initialize with known leads
        initial_map = {"ids": {}, "usernames": {}, "phones": {}}
        for l in INITIAL_LEADS:
            name = l["name"]
            if l.get("id"):
                initial_map["ids"][str(l["id"])] = name
            if l.get("username"):
                initial_map["usernames"][normalize_username(l["username"])] = name
            if l.get("phone"):
                initial_map["phones"][normalize_phone(l["phone"])] = name
        
        self._save(initial_map)
        return initial_map

    def _save(self, data: Dict[str, Any]):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving whitelist: {e}")

    def add_lead(self, name: str, user_id: Optional[int] = None, username: str = "", phone: str = ""):
        data = self.leads
        changed = False
        if user_id:
            uid_str = str(user_id)
            if uid_str not in data.get("ids", {}):
                data.setdefault("ids", {})[uid_str] = name
                changed = True
        if username:
            u_norm = normalize_username(username)
            if u_norm and u_norm not in data.get("usernames", {}):
                data.setdefault("usernames", {})[u_norm] = name
                changed = True
        if phone:
            p_norm = normalize_phone(phone)
            if p_norm and p_norm not in data.get("phones", {}):
                data.setdefault("phones", {})[p_norm] = name
                changed = True
        if changed:
            self.leads = data
            self._save(data)
            logger.info(f"Added new website lead to whitelist: {name} (ID: {user_id}, User: {username}, Phone: {phone})")

    def is_lead(self, user_id: int, username: str = "", phone: str = "") -> bool:
        """
        Returns True ONLY if this person is verified as coming from aiabed.ir website forms
        """
        uid_str = str(user_id)
        if uid_str in self.leads.get("ids", {}):
            return True

        if username:
            u_norm = normalize_username(username)
            if u_norm in self.leads.get("usernames", {}):
                # cache their ID for future quick lookups
                self.add_lead(self.leads["usernames"][u_norm], user_id=user_id)
                return True

        if phone:
            p_norm = normalize_phone(phone)
            if p_norm in self.leads.get("phones", {}):
                # cache their ID for future quick lookups
                self.add_lead(self.leads["phones"][p_norm], user_id=user_id)
                return True

        return False

    def get_lead_name(self, user_id: int, username: str = "", phone: str = "") -> str:
        uid_str = str(user_id)
        if uid_str in self.leads.get("ids", {}):
            return self.leads["ids"][uid_str]
        if username:
            u_norm = normalize_username(username)
            if u_norm in self.leads.get("usernames", {}):
                return self.leads["usernames"][u_norm]
        if phone:
            p_norm = normalize_phone(phone)
            if p_norm in self.leads.get("phones", {}):
                return self.leads["phones"][p_norm]
        return ""

if __name__ == "__main__":
    reg = LeadRegistry()
    print("Roghayeh is lead?", reg.is_lead(34251466, "R_bns"))
    print("Mohammad Feizbakhsh is lead?", reg.is_lead(36395807, "feizbakhsh"))
