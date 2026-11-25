"""
Encrypted State Vault for aiabed-sales-agent
Safely encrypts/decrypts the private data/ JSON files into data_vault.enc
using keys derived exclusively from GitHub Actions Secrets / .env variables.
"""

import os
import sys
import json
import base64
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
VAULT_FILE = BASE_DIR / "data_vault.enc"

STATE_FILES = [
    "conversation_memory.json",
    "website_leads_whitelist.json",
    "processed_contacts.json",
    "phone_calls_todo.json",
    "scheduled_meetings.json",
    "contacts_تماس_با_ما.json",
    "all_website_contacts.json",
]


def _get_fernet() -> Fernet:
    api_hash = os.environ.get("TELEGRAM_API_HASH", "").strip()
    gmail_pwd = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    if not (api_hash and gmail_pwd):
        raise RuntimeError(
            "Missing TELEGRAM_API_HASH or GMAIL_APP_PASSWORD in environment for vault encryption."
        )
    seed = f"{api_hash}:{gmail_pwd}:aiabed-vault-v1".encode("utf-8")
    digest = hashlib.sha256(seed).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def lock():
    """Encrypt data/*.json into data_vault.enc"""
    fernet = _get_fernet()
    bundle = {}
    if DATA_DIR.exists():
        for fname in STATE_FILES:
            fpath = DATA_DIR / fname
            if fpath.exists():
                bundle[fname] = fpath.read_text(encoding="utf-8")
    raw_bytes = json.dumps(bundle, ensure_ascii=False).encode("utf-8")
    encrypted = fernet.encrypt(raw_bytes)
    VAULT_FILE.write_bytes(encrypted)
    print(f"🔒 Vault locked: {len(bundle)} files encrypted into {VAULT_FILE.name} ({len(encrypted)} bytes).")


def unlock():
    """Decrypt data_vault.enc into data/*.json"""
    if not VAULT_FILE.exists():
        print("⚠️ Vault file not found; starting with empty data/ directory.")
        DATA_DIR.mkdir(exist_ok=True)
        return
    fernet = _get_fernet()
    encrypted = VAULT_FILE.read_bytes()
    raw_bytes = fernet.decrypt(encrypted)
    bundle = json.loads(raw_bytes.decode("utf-8"))
    DATA_DIR.mkdir(exist_ok=True)
    for fname, content in bundle.items():
        (DATA_DIR / fname).write_text(content, encoding="utf-8")
    print(f"🔓 Vault unlocked: {len(bundle)} files restored into {DATA_DIR.name}/.")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "lock":
        lock()
    elif action == "unlock":
        unlock()
    else:
        print("Usage: python crypto_state.py [lock|unlock]")
        sys.exit(1)
