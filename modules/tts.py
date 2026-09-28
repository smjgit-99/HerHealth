import io

from gtts import gTTS


def speak(text: str, lang: str):
    """Return MP3 bytes, or None on failure. Nothing is written to disk."""
    try:
        buf = io.BytesIO()
        gTTS(text=text[:1500], lang=lang).write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return None
