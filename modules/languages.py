from gtts.lang import tts_langs

# The app supports exactly three languages.
LANGS = {"English": "en", "Hindi": "hi", "Marathi": "mr"}
_TTS = set(tts_langs())


def can_speak(code: str) -> bool:
    return code in _TTS
