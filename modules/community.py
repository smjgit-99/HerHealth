"""Community logic that has no UI: conditions, rules, safety checks, image clean-up and the sign-in bridge."""
import io
import re
import secrets
import time

from modules import db
from modules.content import load_json

CONDITIONS = load_json("conditions")
BY_ID = {c["id"]: c for c in CONDITIONS}

POST_TYPES = ["Question", "Experience", "Support needed"]
# (key stored in db, label, material icon)
REACTIONS = [("support", "Support", ":material/favorite:"),
             ("relate", "I relate", ":material/handshake:"),
             ("helpful", "Helpful", ":material/lightbulb:")]
REPORT_REASONS = ["Misinformation or unsafe advice", "Harassment or unkind behaviour", "Spam or advertising",
                  "Shares private information", "Something else"]

MAX_POST = 1500
MAX_COMMENT = 500
MAX_IMAGE_BYTES = 3 * 1024 * 1024

DISCLAIMER = "Posts are shared by members and are not medical advice. Please consult a doctor for health concerns."
MED_WARNING = "Please check with your doctor before taking any medicine."
RULES = [
    "Be kind and respectful. Everyone here is dealing with something.",
    "Share your own experience. Do not tell others what medicine to take or what dose to use.",
    "Do not share your name, phone number, address or other private details, yours or anyone else's.",
    "No advertising, selling products or promoting treatments.",
    "Posts are shared by members and are not medical advice. For urgent symptoms, contact a doctor or emergency services.",
]

_MED = re.compile(
    r"\b(\d+(?:\.\d+)?\s?(?:mg|mcg|ml|iu)|dos(?:e|es|age)|tablets?|pills?|capsules?|syrup|injections?|medicines?|medications?|"
    r"prescri\w+|antibiotics?|supplements?|painkillers?|metformin|letrozole|clomid|clomiphene|levothyroxine|thyroxine|"
    r"ibuprofen|paracetamol|acetaminophen|aspirin|naproxen|mefenamic|progesterone|estrogen|oestrogen|birth control|"
    r"contraceptives?|hrt|folic acid|nitrofurantoin|\w+cillin|sertraline|fluoxetine|ssri)\b", re.I)


def looks_like_medicine(text: str) -> bool:
    return bool(_MED.search(text or ""))


def process_image(upload):
    """Validate an uploaded photo and re-encode it. Returns (jpeg_bytes, None) or (None, error).
    Re-encoding strips EXIF data such as GPS location, which matters for privacy."""
    data = upload.getvalue()
    if len(data) > MAX_IMAGE_BYTES:
        return None, "That photo is too large (max 3 MB)."
    try:
        from PIL import Image, ImageOps
        img = Image.open(io.BytesIO(data))
        img.verify()
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
        img.thumbnail((1280, 1280))
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=85)
        return out.getvalue(), None
    except Exception:
        return None, "That file could not be read as a photo. Use a PNG or JPG."


def _alias_for(name: str) -> str:
    """Public display name: first name plus a short number. The real name is never shown to others."""
    base = re.sub(r"[^A-Za-z0-9]", "", (name or "").strip().split(" ")[0])[:12] or "Member"
    while True:
        alias = f"{base}_{secrets.randbelow(9000) + 1000}"
        if not db.one("SELECT 1 FROM users WHERE alias=?", (alias,)):
            return alias


def resolve_user_id(user_data):
    """Map the signed-in Supabase user to a local SQLite user row using email as the source of truth."""
    if not user_data:
        return None
    try:
        # Extract email safely from Supabase user object or dict
        email = getattr(user_data, "email", None) or user_data.get("email", "")
        if not email:
            return None
        email = email.strip().lower()

        # Extract name from metadata if available
        metadata = getattr(user_data, "user_metadata", None) or user_data.get("user_metadata", {})
        name = metadata.get("full_name", "") if metadata else ""

        # Always resolve primarily by email to prevent duplicate rows and ID mismatches
        row = db.one("SELECT id FROM users WHERE email=?", (email,))
        if row:
            return row["id"]

        # If user doesn't exist locally yet, create them
        return db.run(
            "INSERT INTO users(email, alias, salt, pw_hash, created) VALUES(?,?,?,?,?)",
            (email, _alias_for(name), secrets.token_bytes(16), secrets.token_bytes(32), time.time())
        )
    except Exception:
        return None

def ago(ts: float) -> str:
    s = max(0, time.time() - ts)
    if s < 60:
        return "just now"
    if s < 3600:
        return f"{int(s // 60)}m"
    if s < 86400:
        return f"{int(s // 3600)}h"
    return f"{int(s // 86400)}d"