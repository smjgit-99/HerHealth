"""Optional Claude calls. Every function returns None on any failure so callers can fall back."""
import base64
import json
import re

from config import MODEL, get_api_key


def available() -> bool:
    return bool(get_api_key())


def _client():
    import anthropic
    return anthropic.Anthropic(api_key=get_api_key(), timeout=30.0)


def ask_json(system: str, user: str, max_tokens: int = 1500):
    try:
        r = _client().messages.create(
            model=MODEL, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}],
        )
        txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip()
        txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt)
        return json.loads(txt)
    except Exception:
        return None


def vision_text(png_bytes: bytes):
    """Read text from an image with Claude vision."""
    try:
        r = _client().messages.create(
            model=MODEL, max_tokens=2000,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                             "data": base64.b64encode(png_bytes).decode()}},
                {"type": "text", "text": "Transcribe all text in this medical report exactly. Output only the text."},
            ]}],
        )
        return "".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip() or None
    except Exception:
        return None
