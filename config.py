"""Central settings. Change the mascot here."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
APP_TITLE = "HerHealth"

# ---- YOUR CHARACTER: change these three lines ------------------------------
MASCOT_NAME = "Sakhi"
MASCOT_EMOJI = "🌸"                                     # used if no image file
MASCOT_IMAGE = ROOT / "assets" / "mascot" / "mascot.png"  # drop your image here
# ---------------------------------------------------------------------------

TIMEZONE = "Asia/Kolkata"
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")


def get_api_key():
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY") or None
    except Exception:
        return None
