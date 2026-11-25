"""
Link Formatting Utilities for Abdullah Ahmadian's AI Sales Agent
Ensures that all mentions of aiabed.ir are strictly rendered as clickable markdown links
while protecting email addresses and existing markdown links.
Also provides 1-Click WhatsApp direct link generation.
"""

import re
import urllib.parse

def sanitize_customer_name(name: str) -> str:
    """
    Cleans customer name by stripping CRM/bot tags such as:
    'سایت', 'وبسایت', 'مشتری', 'کاربر', parentheses, extra spaces, etc.
    """
    if not name:
        return "همراه گرامی"
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', str(name))
    cleaned = re.sub(r'\b(سایت|وبسایت|مشتری|کاربر|telegram|website)\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("سایت", "").replace("وبسایت", "").strip()
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned or "همراه گرامی"

def ensure_aiabed_links(text: str) -> str:
    """
    Guarantees every mention of aiabed.ir is converted into a clickable markdown link:
    [aiabed.ir](https://aiabed.ir)
    
    Protects:
    1. Email addresses such as aiabed.ir2026@gmail.com or info@aiabed.ir
    2. Existing markdown links like [aiabed.ir](https://aiabed.ir)
    3. Converts raw URLs like https://aiabed.ir to [aiabed.ir](https://aiabed.ir)
    """
    if not text:
        return ""

    # 1. Protect email addresses with placeholder
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    emails = []
    def save_email(m):
        emails.append(m.group(0))
        return f'__EMAIL_PH_{len(emails)-1}__'
    text = re.sub(email_pattern, save_email, text)

    # 2. Protect existing markdown links [label](url)
    md_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    md_links = []
    def save_md(m):
        label, url = m.group(1), m.group(2)
        md_links.append(f'[{label}]({url})')
        return f'__MD_PH_{len(md_links)-1}__'
    text = re.sub(md_pattern, save_md, text)

    # 3. Handle raw URLs like https://aiabed.ir or http://aiabed.ir
    raw_url_pattern = r'https?://(?:www\.)?aiabed\.ir(/[^\s)]*)?'
    urls = []
    def save_raw_url(m):
        path = m.group(1) or ""
        full_url = f"https://aiabed.ir{path}"
        urls.append(full_url)
        return f'__RAW_URL_PH_{len(urls)-1}__'
    text = re.sub(raw_url_pattern, save_raw_url, text)

    # 4. Convert any remaining bare 'aiabed.ir' or 'www.aiabed.ir'
    text = re.sub(r'(?i)\b(?:www\.)?aiabed\.ir\b', '[aiabed.ir](https://aiabed.ir)', text)

    # 5. Restore raw URLs converted to markdown links
    for i, url in enumerate(urls):
        text = text.replace(f'__RAW_URL_PH_{i}__', f'[aiabed.ir]({url})')

    # 6. Restore existing markdown links
    for i, link in enumerate(md_links):
        text = text.replace(f'__MD_PH_{i}__', link)

    # 7. Restore protected email addresses
    for i, email in enumerate(emails):
        text = text.replace(f'__EMAIL_PH_{i}__', email)

    return text

def generate_whatsapp_link(phone: str, text: str) -> str:
    """
    Generates a 1-click WhatsApp wa.me direct chat link with pre-filled message text.
    No need to save contact in phonebook.
    """
    clean_digits = re.sub(r"[^\d]", "", str(phone))
    if clean_digits.startswith("09"):
        clean_digits = "98" + clean_digits[1:]
    elif clean_digits.startswith("98"):
        pass
    encoded = urllib.parse.quote(text)
    return f"https://wa.me/{clean_digits}?text={encoded}"

if __name__ == "__main__":
    link = generate_whatsapp_link("09161002550", "سلام مهندس احمدیان عزیز 🌹")
    print("Test WhatsApp Link:", link)
