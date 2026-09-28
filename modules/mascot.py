import streamlit as st

from config import MASCOT_EMOJI, MASCOT_IMAGE, MASCOT_NAME


def avatar():
    return str(MASCOT_IMAGE) if MASCOT_IMAGE.exists() else MASCOT_EMOJI


def say(text: str):
    with st.chat_message(MASCOT_NAME, avatar=avatar()):
        st.write(text)
